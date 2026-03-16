from uuid import UUID

from fastapi import APIRouter, Depends

from api.dependencies import require_role
from api.schemas.hce import ConsultaCreateRequest, ConsultaResponse, HCEResponse
from apps.hce.services import create_consulta, get_consulta, get_hce_with_consultas

router = APIRouter(prefix="/hce", tags=["hce"])


@router.get("/{paciente_id}/", response_model=HCEResponse)
def get_hce(
    paciente_id: UUID,
    user=Depends(require_role("doctora")),
):
    hce = get_hce_with_consultas(paciente_id, user)

    consultas = []
    for c in hce.consultas.all():
        sv = getattr(c, "signos_vitales", None)
        consultas.append(
            {
                "id": c.id,
                "tipo_consulta_id": c.tipo_consulta_id,
                "fecha_hora": c.fecha_hora,
                "motivo_consulta": c.motivo_consulta,
                "examen_fisico": c.examen_fisico,
                "plan_terapeutico": c.plan_terapeutico,
                "modalidad": c.modalidad,
                "signos_vitales": sv,
                "medicamentos": list(c.medicamentos.all()),
                "created_at": c.created_at,
            }
        )

    return {
        "id": hce.id,
        "paciente_id": hce.paciente_id,
        "consultas": consultas,
        "created_at": hce.created_at,
    }


@router.post("/consultas/", response_model=ConsultaResponse, status_code=201)
def create_consulta_route(
    body: ConsultaCreateRequest,
    user=Depends(require_role("doctora")),
):
    data = body.model_dump()
    # Flatten signos_vitales dict so the service can unpack it
    if data.get("signos_vitales"):
        data["signos_vitales"] = {
            k: v for k, v in data["signos_vitales"].items() if v is not None
        }
    consulta = create_consulta(data, user)
    sv = getattr(consulta, "signos_vitales", None)
    return {
        "id": consulta.id,
        "tipo_consulta_id": consulta.tipo_consulta_id,
        "fecha_hora": consulta.fecha_hora,
        "motivo_consulta": consulta.motivo_consulta,
        "examen_fisico": consulta.examen_fisico,
        "plan_terapeutico": consulta.plan_terapeutico,
        "modalidad": consulta.modalidad,
        "signos_vitales": sv,
        "medicamentos": list(consulta.medicamentos.all()),
        "created_at": consulta.created_at,
    }


@router.get("/consultas/{consulta_id}/", response_model=ConsultaResponse)
def get_consulta_route(
    consulta_id: UUID,
    user=Depends(require_role("doctora")),
):
    consulta = get_consulta(consulta_id, user)
    sv = getattr(consulta, "signos_vitales", None)
    return {
        "id": consulta.id,
        "tipo_consulta_id": consulta.tipo_consulta_id,
        "fecha_hora": consulta.fecha_hora,
        "motivo_consulta": consulta.motivo_consulta,
        "examen_fisico": consulta.examen_fisico,
        "plan_terapeutico": consulta.plan_terapeutico,
        "modalidad": consulta.modalidad,
        "signos_vitales": sv,
        "medicamentos": list(consulta.medicamentos.all()),
        "created_at": consulta.created_at,
    }
