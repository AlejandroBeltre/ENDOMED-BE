from datetime import date
from uuid import UUID

from django.utils import timezone as tz

from apps.agenda.models import Cita, TipoConsulta
from apps.authentication.models import User
from apps.authentication.services import get_allowed_sede_ids, validate_sede_access


def create_tipo_consulta(data: dict) -> TipoConsulta:
    from fastapi import HTTPException

    if TipoConsulta.objects.filter(nombre__iexact=data["nombre"]).exists():
        raise HTTPException(400, "Ya existe un tipo de consulta con ese nombre.")
    return TipoConsulta.objects.create(
        nombre=data["nombre"],
        duracion_min=data["duracion_min"],
        tarifa_rd=data["tarifa_rd"],
        color_hex=data["color_hex"],
    )


def update_tipo_consulta(tipo_id: UUID, data: dict) -> TipoConsulta:
    from fastapi import HTTPException

    try:
        tipo = TipoConsulta.objects.get(id=tipo_id)
    except TipoConsulta.DoesNotExist:
        raise HTTPException(404, "Tipo de consulta no encontrado.")

    update_fields = []
    for field in ("nombre", "duracion_min", "tarifa_rd", "color_hex"):
        if field in data and data[field] is not None:
            setattr(tipo, field, data[field])
            update_fields.append(field)

    if update_fields:
        update_fields.append("updated_at")
        tipo.save(update_fields=update_fields)
    return tipo


def _active_citas():
    return Cita.objects.filter(deleted_at__isnull=True)


def get_citas_hoy(user: User, sede_id: UUID | None, profesional_id: UUID | None):
    today = tz.localdate()
    qs = (
        _active_citas()
        .select_related("paciente", "profesional", "tipo_consulta", "sede")
        .filter(fecha_hora__date=today)
    )

    allowed = get_allowed_sede_ids(user)
    qs = qs.filter(sede_id__in=allowed)

    if sede_id:
        qs = qs.filter(sede_id=sede_id)
    if profesional_id:
        qs = qs.filter(profesional_id=profesional_id)

    return qs.order_by("fecha_hora")


def list_citas(
    user: User,
    fecha: date | None,
    sede_id: UUID | None,
    profesional_id: UUID | None,
):
    qs = _active_citas().select_related(
        "paciente", "profesional", "tipo_consulta", "sede"
    )

    allowed = get_allowed_sede_ids(user)
    qs = qs.filter(sede_id__in=allowed)

    if fecha:
        qs = qs.filter(fecha_hora__date=fecha)
    if sede_id:
        qs = qs.filter(sede_id=sede_id)
    if profesional_id:
        qs = qs.filter(profesional_id=profesional_id)

    return qs.order_by("fecha_hora")


def create_cita(data: dict, user: User) -> Cita:
    if not validate_sede_access(user, data["sede_id"]):
        from fastapi import HTTPException

        raise HTTPException(403, "No tiene acceso a esa sede.")

    cita = Cita.objects.create(
        paciente_id=data["paciente_id"],
        sede_id=data["sede_id"],
        profesional_id=data["profesional_id"],
        tipo_consulta_id=data["tipo_consulta_id"],
        fecha_hora=data["fecha_hora"],
        duracion_min=data["duracion_min"],
        modalidad=data.get("modalidad", Cita.Modalidad.PRESENCIAL),
        notas_previas=data.get("notas_previas", ""),
    )

    # Schedule WhatsApp + email reminders asynchronously
    try:
        from tasks.recordatorios import programar_recordatorios_cita

        programar_recordatorios_cita(cita.id)
    except Exception:
        pass  # Celery may be unavailable in dev — don't fail the request

    return cita


def get_cita(cita_id: UUID, user: User) -> Cita:
    from fastapi import HTTPException

    allowed = get_allowed_sede_ids(user)
    try:
        return (
            _active_citas()
            .select_related("paciente", "profesional", "tipo_consulta", "sede")
            .get(id=cita_id, sede_id__in=allowed)
        )
    except Cita.DoesNotExist:
        raise HTTPException(404, "Cita no encontrada.")


def update_cita_estado(cita_id: UUID, estado: str, user: User) -> Cita:
    from fastapi import HTTPException

    valid = {c.value for c in Cita.Estado}
    if estado not in valid:
        raise HTTPException(400, f"Estado inválido. Opciones: {', '.join(valid)}")

    cita = get_cita(cita_id, user)
    cita.estado = estado
    cita.save(update_fields=["estado", "updated_at"])

    if estado == Cita.Estado.CONFIRMADA:
        try:
            from tasks.recordatorios import programar_recordatorios_cita

            programar_recordatorios_cita(cita.id)
        except Exception:
            pass

    return cita
