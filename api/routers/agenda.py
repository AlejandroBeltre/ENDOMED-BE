from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends

from api.dependencies import get_current_user
from api.schemas.agenda import (
    CitaCreateRequest,
    CitaResponse,
    EstadoCitaRequest,
    TipoConsultaResponse,
)
from apps.agenda.models import TipoConsulta as TipoConsultaModel
from apps.agenda.services import (
    create_cita,
    get_cita,
    get_citas_hoy,
    list_citas,
    update_cita_estado,
)

router = APIRouter(prefix="/agenda", tags=["agenda"])


@router.get("/tipos-consulta/", response_model=list[TipoConsultaResponse])
def list_tipos_consulta(user=Depends(get_current_user)):
    return list(TipoConsultaModel.objects.all())


@router.get("/hoy/", response_model=list[CitaResponse])
def citas_hoy(
    sede_id: UUID | None = None,
    profesional_id: UUID | None = None,
    user=Depends(get_current_user),
):
    return list(get_citas_hoy(user, sede_id, profesional_id))


@router.get("/citas/", response_model=list[CitaResponse])
def list_citas_route(
    fecha: date | None = None,
    sede_id: UUID | None = None,
    profesional_id: UUID | None = None,
    user=Depends(get_current_user),
):
    return list(list_citas(user, fecha, sede_id, profesional_id))


@router.post("/citas/", response_model=CitaResponse, status_code=201)
def create_cita_route(
    body: CitaCreateRequest,
    user=Depends(get_current_user),
):
    return create_cita(body.model_dump(), user)


@router.get("/citas/{cita_id}/", response_model=CitaResponse)
def get_cita_route(cita_id: UUID, user=Depends(get_current_user)):
    return get_cita(cita_id, user)


@router.patch("/citas/{cita_id}/estado/", response_model=CitaResponse)
def update_estado_route(
    cita_id: UUID,
    body: EstadoCitaRequest,
    user=Depends(get_current_user),
):
    return update_cita_estado(cita_id, body.estado, user)
