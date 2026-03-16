from uuid import UUID

from apps.authentication.models import User
from apps.hce.models import (
    Consulta,
    HistoriaClinica,
    MedicamentoPrescrito,
    SignosVitales,
)
from apps.pacientes.services import get_paciente


def get_or_create_hce(paciente_id: UUID, user: User) -> HistoriaClinica:
    paciente = get_paciente(paciente_id, user)
    hce, _ = HistoriaClinica.objects.get_or_create(paciente=paciente)
    return hce


def create_consulta(data: dict, user: User) -> Consulta:
    from fastapi import HTTPException

    hce = get_or_create_hce(data["paciente_id"], user)

    # Validate cita belongs to this patient if provided
    if data.get("cita_id"):
        from apps.agenda.models import Cita

        try:
            cita = Cita.objects.get(id=data["cita_id"], paciente=hce.paciente)
        except Cita.DoesNotExist:
            raise HTTPException(404, "Cita no encontrada para este paciente.")
    else:
        cita = None

    consulta = Consulta.objects.create(
        hce=hce,
        cita=cita,
        tipo_consulta_id=data["tipo_consulta_id"],
        fecha_hora=data["fecha_hora"],
        motivo_consulta=data["motivo_consulta"],
        examen_fisico=data.get("examen_fisico", {}),
        plan_terapeutico=data.get("plan_terapeutico", ""),
        modalidad=data.get("modalidad", "presencial"),
        created_by=user,
    )

    # Signos vitales
    sv_data = data.get("signos_vitales")
    if sv_data:
        SignosVitales.objects.create(consulta=consulta, **sv_data)

    # Medicamentos
    for med in data.get("medicamentos", []):
        MedicamentoPrescrito.objects.create(consulta=consulta, **med)

    # Mark linked cita as completada
    if cita and cita.estado != "completada":
        cita.estado = "completada"
        cita.save(update_fields=["estado", "updated_at"])

    return _load_consulta(consulta.id)


def get_consulta(consulta_id: UUID, user: User) -> Consulta:
    from fastapi import HTTPException

    from apps.authentication.services import get_allowed_sede_ids

    allowed_sedes = get_allowed_sede_ids(user)
    try:
        return _load_consulta(consulta_id, sede_ids=allowed_sedes)
    except Consulta.DoesNotExist:
        raise HTTPException(404, "Consulta no encontrada.")


def get_hce_with_consultas(paciente_id: UUID, user: User) -> HistoriaClinica:
    hce = get_or_create_hce(paciente_id, user)
    # Prefetch active consultas with related objects
    from django.db.models import Prefetch

    return HistoriaClinica.objects.prefetch_related(
        Prefetch(
            "consultas",
            queryset=Consulta.objects.filter(deleted_at__isnull=True)
            .select_related("tipo_consulta")
            .prefetch_related("signos_vitales", "medicamentos")
            .order_by("-fecha_hora"),
        )
    ).get(id=hce.id)


def _load_consulta(consulta_id: UUID, sede_ids=None) -> Consulta:
    qs = (
        Consulta.objects.filter(deleted_at__isnull=True)
        .select_related("tipo_consulta")
        .prefetch_related("signos_vitales", "medicamentos")
    )
    if sede_ids is not None:
        qs = qs.filter(hce__paciente__sede_id__in=sede_ids)
    return qs.get(id=consulta_id)
