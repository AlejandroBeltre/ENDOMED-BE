from uuid import UUID

from fastapi import APIRouter, Depends

from api.dependencies import get_current_user
from api.schemas.pacientes import PacienteCreateRequest, PacienteResponse
from apps.pacientes.services import create_paciente, get_paciente, search_pacientes

router = APIRouter(prefix="/pacientes", tags=["pacientes"])


@router.get("/", response_model=list[PacienteResponse])
def list_pacientes(
    q: str | None = None,
    sede_id: UUID | None = None,
    user=Depends(get_current_user),
):
    return list(search_pacientes(user, q, sede_id))


@router.post("/", response_model=PacienteResponse, status_code=201)
def create_paciente_route(
    body: PacienteCreateRequest,
    user=Depends(get_current_user),
):
    return create_paciente(body.model_dump(), user)


@router.get("/{paciente_id}/", response_model=PacienteResponse)
def get_paciente_route(paciente_id: UUID, user=Depends(get_current_user)):
    return get_paciente(paciente_id, user)
