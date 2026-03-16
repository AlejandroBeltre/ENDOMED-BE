from uuid import UUID

from django.db.models import Q

from apps.authentication.models import User
from apps.authentication.services import get_allowed_sede_ids, validate_sede_access
from apps.pacientes.models import Paciente


def _active_pacientes():
    return Paciente.objects.filter(deleted_at__isnull=True)


def search_pacientes(user: User, q: str | None, sede_id: UUID | None):
    allowed = get_allowed_sede_ids(user)
    qs = _active_pacientes().filter(sede_id__in=allowed).select_related("sede")

    if sede_id:
        qs = qs.filter(sede_id=sede_id)

    if q:
        qs = qs.filter(
            Q(nombre__icontains=q) | Q(apellido__icontains=q) | Q(cedula__icontains=q)
        )

    return qs.order_by("apellido", "nombre")


def create_paciente(data: dict, user: User) -> Paciente:
    from fastapi import HTTPException

    if not validate_sede_access(user, data["sede_id"]):
        raise HTTPException(403, "No tiene acceso a esa sede.")

    if Paciente.objects.filter(cedula=data["cedula"]).exists():
        raise HTTPException(409, "Ya existe un paciente con esa cédula.")

    return Paciente.objects.create(
        cedula=data["cedula"],
        nombre=data["nombre"],
        apellido=data["apellido"],
        fecha_nacimiento=data["fecha_nacimiento"],
        sexo=data["sexo"],
        telefono_whatsapp=data["telefono_whatsapp"],
        email=data.get("email", ""),
        sede_id=data["sede_id"],
    )


def get_paciente(paciente_id: UUID, user: User) -> Paciente:
    from fastapi import HTTPException

    allowed = get_allowed_sede_ids(user)
    try:
        return _active_pacientes().get(id=paciente_id, sede_id__in=allowed)
    except Paciente.DoesNotExist:
        raise HTTPException(404, "Paciente no encontrado.")
