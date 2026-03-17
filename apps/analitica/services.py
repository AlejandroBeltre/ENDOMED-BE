"""Analytics query services.

All queries run against the actual tables (not the materialized views) so that
endpoint responses are always up-to-date.  The materialized views exist for
heavy offline reporting and are NOT queried here.
"""

import csv
import io
from datetime import date
from decimal import Decimal
from uuid import UUID

from django.core.cache import cache
from django.db.models import Count, Sum
from django.utils import timezone as tz

from apps.authentication.models import User
from apps.authentication.services import get_allowed_sede_ids

_CACHE_TTL = 30 * 60  # 30 minutes


def _cache_key(*parts: object) -> str:
    return "analitica:" + ":".join(str(p) for p in parts)


# ── helpers ───────────────────────────────────────────────────────────────────


def _date_range(meses: int | None) -> tuple[date | None, date | None]:
    """Return (fecha_desde, None) for the requested number of months back."""
    if not meses:
        return None, None
    from dateutil.relativedelta import relativedelta

    hasta = tz.localdate()
    desde = hasta - relativedelta(months=meses)
    return desde, hasta


# ── resumen (KPIs) ────────────────────────────────────────────────────────────


def get_resumen(user: User, sede_id: UUID | None) -> dict:
    key = _cache_key("resumen", user.id, sede_id)
    cached = cache.get(key)
    if cached is not None:
        return cached

    from apps.agenda.models import Cita
    from apps.finanzas.models import Factura
    from apps.pacientes.models import Paciente

    allowed = get_allowed_sede_ids(user)
    today = tz.localdate()
    mes_inicio = today.replace(day=1)

    # Scope by sede
    pacientes_qs = Paciente.objects.filter(sede_id__in=allowed, deleted_at__isnull=True)
    citas_qs = Cita.objects.filter(sede_id__in=allowed, deleted_at__isnull=True)
    facturas_qs = Factura.objects.filter(sede_id__in=allowed, deleted_at__isnull=True)

    if sede_id:
        pacientes_qs = pacientes_qs.filter(sede_id=sede_id)
        citas_qs = citas_qs.filter(sede_id=sede_id)
        facturas_qs = facturas_qs.filter(sede_id=sede_id)

    total_pacientes = pacientes_qs.count()
    consultas_mes = citas_qs.filter(
        fecha_hora__date__gte=mes_inicio, estado="completada"
    ).count()
    ingresos_mes = facturas_qs.filter(fecha__gte=mes_inicio, estado="pagada").aggregate(
        total=Sum("total_rd")
    )["total"] or Decimal(0)
    citas_hoy = citas_qs.filter(
        fecha_hora__date=today, estado__in=["pendiente", "confirmada"]
    ).count()

    result = {
        "total_pacientes": total_pacientes,
        "consultas_este_mes": consultas_mes,
        "ingresos_este_mes": ingresos_mes,
        "citas_hoy": citas_hoy,
    }
    cache.set(key, result, _CACHE_TTL)
    return result


# ── diagnósticos ──────────────────────────────────────────────────────────────


def get_diagnosticos(
    user: User,
    sede_id: UUID | None,
    meses: int | None,
) -> list[dict]:
    key = _cache_key("diagnosticos", user.id, sede_id, meses)
    cached = cache.get(key)
    if cached is not None:
        return cached

    from apps.hce.models import DiagnosticoConsulta

    allowed = get_allowed_sede_ids(user)
    desde, _ = _date_range(meses)

    qs = DiagnosticoConsulta.objects.filter(
        tipo="principal",
        consulta__deleted_at__isnull=True,
    )

    # sede scope via cita or patient sede
    qs = qs.filter(
        consulta__hce__paciente__sede_id__in=allowed,
    )
    if sede_id:
        qs = qs.filter(consulta__hce__paciente__sede_id=sede_id)
    if desde:
        qs = qs.filter(consulta__fecha_hora__date__gte=desde)

    result = list(
        qs.values("codigo_cie10", "descripcion")
        .annotate(frecuencia=Count("id"))
        .order_by("-frecuencia")[:10]
    )
    cache.set(key, result, _CACHE_TTL)
    return result


# ── demografía ────────────────────────────────────────────────────────────────


def get_demografia(user: User, sede_id: UUID | None) -> list[dict]:
    key = _cache_key("demografia", user.id, sede_id)
    cached = cache.get(key)
    if cached is not None:
        return cached

    from apps.pacientes.models import Paciente

    allowed = get_allowed_sede_ids(user)
    qs = Paciente.objects.filter(sede_id__in=allowed, deleted_at__isnull=True)
    if sede_id:
        qs = qs.filter(sede_id=sede_id)

    today = tz.localdate()
    rows = []
    for grupo, min_age, max_age in [
        ("0-17", 0, 17),
        ("18-29", 18, 29),
        ("30-44", 30, 44),
        ("45-59", 45, 59),
        ("60+", 60, 200),
    ]:
        desde_nac = date(today.year - max_age - 1, today.month, today.day)
        hasta_nac = date(today.year - min_age, today.month, today.day)
        base = qs.filter(
            fecha_nacimiento__gte=desde_nac,
            fecha_nacimiento__lte=hasta_nac,
        )
        masculino = base.filter(sexo="M").count()
        femenino = base.filter(sexo="F").count()
        rows.append(
            {
                "grupo_etario": grupo,
                "masculino": masculino,
                "femenino": femenino,
                "total": masculino + femenino,
            }
        )
    cache.set(key, rows, _CACHE_TTL)
    return rows


# ── prevalencia ───────────────────────────────────────────────────────────────


def get_prevalencia(
    user: User,
    sede_id: UUID | None,
    patologia: str | None,
    meses: int | None,
) -> list[dict]:
    key = _cache_key("prevalencia", user.id, sede_id, patologia, meses)
    cached = cache.get(key)
    if cached is not None:
        return cached

    from apps.hce.models import DiagnosticoConsulta

    allowed = get_allowed_sede_ids(user)
    desde, _ = _date_range(meses or 12)

    qs = DiagnosticoConsulta.objects.filter(
        tipo="principal",
        consulta__deleted_at__isnull=True,
        consulta__hce__paciente__sede_id__in=allowed,
    )
    if sede_id:
        qs = qs.filter(consulta__hce__paciente__sede_id=sede_id)
    if desde:
        qs = qs.filter(consulta__fecha_hora__date__gte=desde)
    if patologia:
        qs = qs.filter(codigo_cie10__istartswith=patologia)

    from django.db.models.functions import TruncMonth

    result = list(
        qs.annotate(mes=TruncMonth("consulta__fecha_hora"))
        .values("mes", "codigo_cie10", "descripcion")
        .annotate(frecuencia=Count("id"))
        .order_by("mes", "-frecuencia")
    )
    cache.set(key, result, _CACHE_TTL)
    return result


# ── rendimiento ───────────────────────────────────────────────────────────────


def get_rendimiento(
    user: User,
    sede_id: UUID | None,
    meses: int | None,
) -> list[dict]:
    key = _cache_key("rendimiento", user.id, sede_id, meses)
    cached = cache.get(key)
    if cached is not None:
        return cached

    from apps.agenda.models import Cita
    from apps.finanzas.models import Factura

    allowed = get_allowed_sede_ids(user)
    desde, _ = _date_range(meses or 3)

    citas_qs = Cita.objects.filter(
        sede_id__in=allowed,
        deleted_at__isnull=True,
        estado="completada",
    )
    facturas_qs = Factura.objects.filter(
        sede_id__in=allowed,
        deleted_at__isnull=True,
    )

    if sede_id:
        citas_qs = citas_qs.filter(sede_id=sede_id)
        facturas_qs = facturas_qs.filter(sede_id=sede_id)
    if desde:
        citas_qs = citas_qs.filter(fecha_hora__date__gte=desde)
        facturas_qs = facturas_qs.filter(fecha__gte=desde)

    vol_por_tipo = {
        row["tipo_consulta__nombre"]: row["total"]
        for row in citas_qs.values("tipo_consulta__nombre").annotate(total=Count("id"))
    }
    ing_por_tipo = {
        row["cita__tipo_consulta__nombre"]: row["total"]
        for row in facturas_qs.filter(cita__isnull=False)
        .values("cita__tipo_consulta__nombre")
        .annotate(total=Sum("total_rd"))
    }

    tipos = set(vol_por_tipo) | set(ing_por_tipo)
    result = [
        {
            "tipo_consulta": t,
            "volumen": vol_por_tipo.get(t, 0),
            "ingresos": ing_por_tipo.get(t, Decimal(0)),
        }
        for t in sorted(tipos)
    ]
    cache.set(key, result, _CACHE_TTL)
    return result


# ── exportar CSV ──────────────────────────────────────────────────────────────


def exportar_csv(
    user: User,
    tipo: str,
    sede_id: UUID | None,
    meses: int | None,
) -> str:
    """Return CSV string for the requested analytics type."""
    dispatch = {
        "diagnosticos": lambda: get_diagnosticos(user, sede_id, meses),
        "demografia": lambda: get_demografia(user, sede_id),
        "prevalencia": lambda: get_prevalencia(user, sede_id, None, meses),
        "rendimiento": lambda: get_rendimiento(user, sede_id, meses),
    }
    if tipo not in dispatch:
        from fastapi import HTTPException

        raise HTTPException(
            400,
            f"Tipo inválido. Opciones: {', '.join(dispatch)}",
        )

    rows = dispatch[tipo]()
    if not rows:
        return ""

    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue()
