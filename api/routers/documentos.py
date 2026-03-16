from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from api.dependencies import require_role
from api.schemas.documentos import RecetaRequest
from apps.documentos.services import generar_receta_pdf

router = APIRouter(prefix="/documentos", tags=["documentos"])


@router.post("/receta/")
def crear_receta(
    body: RecetaRequest,
    user=Depends(require_role("doctora")),
):
    """
    Generates and returns a prescription PDF for the given consulta.
    Restricted to role=doctora.
    """
    try:
        pdf_bytes = generar_receta_pdf(str(body.consulta_id), user)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="receta_{body.consulta_id}.pdf"'
        },
    )
