from datetime import date
from decimal import Decimal
from uuid import UUID

from django.db.models import F, Sum
from django.utils import timezone as tz

from apps.authentication.models import User
from apps.authentication.services import get_allowed_sede_ids, validate_sede_access
from apps.finanzas.models import Factura, Inventario, MovimientoInventario, Pago

# ── helpers ──────────────────────────────────────────────────────────────────


def _next_numero_factura() -> int:
    from django.db import connection

    with connection.cursor() as cursor:
        cursor.execute("SELECT nextval('factura_numero_seq')")
        return cursor.fetchone()[0]


def _active_facturas():
    return Factura.objects.filter(deleted_at__isnull=True)


# ── caja ─────────────────────────────────────────────────────────────────────


def get_caja_hoy(user: User, sede_id: UUID | None) -> dict:
    """Return today's transactions for the user's allowed sedes."""
    today = tz.localdate()
    allowed = get_allowed_sede_ids(user)

    qs = (
        _active_facturas()
        .select_related("paciente", "cita__tipo_consulta")
        .prefetch_related("pagos")
        .filter(fecha=today, sede_id__in=allowed)
    )
    if sede_id:
        qs = qs.filter(sede_id=sede_id)

    facturas = list(qs.order_by("created_at"))

    total_general = sum(f.total_rd for f in facturas)
    total_pagado = sum(p.monto_rd for f in facturas for p in f.pagos.all())

    return {
        "fecha": today,
        "facturas": facturas,
        "total_general": total_general,
        "total_pagado": total_pagado,
    }


# ── facturas ─────────────────────────────────────────────────────────────────


def list_facturas(
    user: User,
    sede_id: UUID | None,
    estado: str | None,
    fecha_desde: date | None,
    fecha_hasta: date | None,
) -> list[Factura]:
    allowed = get_allowed_sede_ids(user)
    qs = (
        _active_facturas()
        .select_related("paciente", "sede", "cita__tipo_consulta", "created_by")
        .filter(sede_id__in=allowed)
    )
    if sede_id:
        qs = qs.filter(sede_id=sede_id)
    if estado:
        qs = qs.filter(estado=estado)
    if fecha_desde:
        qs = qs.filter(fecha__gte=fecha_desde)
    if fecha_hasta:
        qs = qs.filter(fecha__lte=fecha_hasta)
    return list(qs.order_by("-fecha", "-created_at"))


def create_factura(data: dict, user: User) -> Factura:
    from fastapi import HTTPException

    if not validate_sede_access(user, data["sede_id"]):
        raise HTTPException(403, "No tiene acceso a esa sede.")

    subtotal = Decimal(str(data["subtotal_rd"]))
    descuento = Decimal(str(data.get("descuento_rd", 0)))
    itbis = Decimal(str(data.get("itbis_rd", 0)))
    total = subtotal - descuento + itbis

    if total < 0:
        raise HTTPException(400, "El total no puede ser negativo.")

    return Factura.objects.create(
        numero_factura=_next_numero_factura(),
        paciente_id=data["paciente_id"],
        cita_id=data.get("cita_id"),
        sede_id=data["sede_id"],
        fecha=data["fecha"],
        subtotal_rd=subtotal,
        descuento_rd=descuento,
        itbis_rd=itbis,
        total_rd=total,
        estado=Factura.Estado.BORRADOR,
        seguro_id=data.get("seguro_id"),
        created_by=user,
    )


def get_factura(factura_id: UUID, user: User) -> Factura:
    from fastapi import HTTPException

    allowed = get_allowed_sede_ids(user)
    try:
        return (
            _active_facturas()
            .select_related("paciente", "sede", "cita__tipo_consulta", "created_by")
            .prefetch_related("pagos__registrado_por")
            .get(id=factura_id, sede_id__in=allowed)
        )
    except Factura.DoesNotExist:
        raise HTTPException(404, "Factura no encontrada.")


def update_factura_estado(factura_id: UUID, estado: str, user: User) -> Factura:
    from fastapi import HTTPException

    valid = {c.value for c in Factura.Estado}
    if estado not in valid:
        raise HTTPException(400, f"Estado inválido. Opciones: {', '.join(valid)}")

    factura = get_factura(factura_id, user)

    if factura.estado == Factura.Estado.ANULADA:
        raise HTTPException(
            400, "No se puede cambiar el estado de una factura anulada."
        )

    factura.estado = estado
    factura.save(update_fields=["estado", "updated_at"])
    return factura


# ── pagos ─────────────────────────────────────────────────────────────────────


def create_pago(data: dict, user: User) -> Pago:
    from fastapi import HTTPException

    factura = get_factura(data["factura_id"], user)

    if factura.estado == Factura.Estado.ANULADA:
        raise HTTPException(
            400, "No se puede registrar un pago en una factura anulada."
        )

    pago = Pago.objects.create(
        factura=factura,
        monto_rd=Decimal(str(data["monto_rd"])),
        metodo=data["metodo"],
        referencia_transaccion=data.get("referencia_transaccion", ""),
        fecha_pago=data["fecha_pago"],
        registrado_por=user,
    )

    # Auto-transition: if total pagado cubre el total, marcar como pagada
    total_pagado = factura.pagos.aggregate(total=Sum("monto_rd"))["total"] or Decimal(0)
    if total_pagado >= factura.total_rd and factura.estado != Factura.Estado.PAGADA:
        factura.estado = Factura.Estado.PAGADA
        factura.save(update_fields=["estado", "updated_at"])

    return pago


# ── inventario ────────────────────────────────────────────────────────────────


def list_inventario(user: User) -> list[Inventario]:
    return list(Inventario.objects.all().order_by("nombre_producto"))


def create_inventario(data: dict, user: User) -> Inventario:
    return Inventario.objects.create(
        nombre_producto=data["nombre_producto"],
        categoria=data["categoria"],
        stock_actual=data.get("stock_actual", 0),
        stock_minimo=data.get("stock_minimo", 0),
        precio_unitario_rd=Decimal(str(data["precio_unitario_rd"])),
        proveedor=data.get("proveedor", ""),
    )


def update_inventario(item_id: UUID, data: dict, user: User) -> Inventario:
    from fastapi import HTTPException

    try:
        item = Inventario.objects.get(id=item_id)
    except Inventario.DoesNotExist:
        raise HTTPException(404, "Ítem de inventario no encontrado.")

    fields_to_update = []
    for field in (
        "nombre_producto",
        "categoria",
        "stock_minimo",
        "precio_unitario_rd",
        "proveedor",
    ):
        if field in data and data[field] is not None:
            setattr(item, field, data[field])
            fields_to_update.append(field)

    if fields_to_update:
        fields_to_update.append("updated_at")
        item.save(update_fields=fields_to_update)

    return item


def create_movimiento_inventario(
    item_id: UUID, data: dict, user: User
) -> MovimientoInventario:
    from django.db import transaction
    from fastapi import HTTPException

    tipo = data["tipo"]
    cantidad = int(data["cantidad"])

    if cantidad <= 0:
        raise HTTPException(400, "La cantidad debe ser mayor a 0.")

    with transaction.atomic():
        try:
            item = Inventario.objects.select_for_update().get(id=item_id)
        except Inventario.DoesNotExist:
            raise HTTPException(404, "Ítem de inventario no encontrado.")

        # Apply stock change
        if tipo == MovimientoInventario.Tipo.ENTRADA:
            item.stock_actual = F("stock_actual") + cantidad
        elif tipo == MovimientoInventario.Tipo.SALIDA:
            if item.stock_actual < cantidad:
                raise HTTPException(400, "Stock insuficiente para la salida.")
            item.stock_actual = F("stock_actual") - cantidad
        else:  # ajuste — cantidad es el nuevo stock absoluto
            item.stock_actual = cantidad

        item.save(update_fields=["stock_actual", "updated_at"])
        item.refresh_from_db()

        return MovimientoInventario.objects.create(
            inventario=item,
            tipo=tipo,
            cantidad=cantidad,
            motivo=data["motivo"],
            consulta_id=data.get("consulta_id"),
            created_by=user,
        )


# ── reportes ──────────────────────────────────────────────────────────────────


def get_reportes(
    user: User,
    sede_id: UUID | None,
    fecha_desde: date | None,
    fecha_hasta: date | None,
) -> dict:
    allowed = get_allowed_sede_ids(user)
    qs = _active_facturas().filter(sede_id__in=allowed)

    if sede_id:
        qs = qs.filter(sede_id=sede_id)
    if fecha_desde:
        qs = qs.filter(fecha__gte=fecha_desde)
    if fecha_hasta:
        qs = qs.filter(fecha__lte=fecha_hasta)

    # Income by sede
    por_sede = list(
        qs.values("sede__nombre")
        .annotate(total=Sum("total_rd"))
        .order_by("sede__nombre")
    )

    # Income by tipo_consulta (requires join through cita)
    por_tipo = list(
        qs.filter(cita__isnull=False)
        .values("cita__tipo_consulta__nombre")
        .annotate(total=Sum("total_rd"))
        .order_by("-total")
    )

    # Income by estado
    por_estado = list(
        qs.values("estado").annotate(total=Sum("total_rd")).order_by("estado")
    )

    total_general = qs.aggregate(total=Sum("total_rd"))["total"] or Decimal(0)

    return {
        "total_general": total_general,
        "por_sede": por_sede,
        "por_tipo_consulta": por_tipo,
        "por_estado": por_estado,
    }
