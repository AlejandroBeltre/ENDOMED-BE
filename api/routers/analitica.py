from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse

from api.dependencies import require_role
from api.schemas.analitica import (
    DemografiaGrupoResponse,
    DiagnosticoRankedResponse,
    PrevalenciaPuntoResponse,
    RendimientoTipoResponse,
    ResumenKPIsResponse,
)
from apps.analitica.services import (
    exportar_csv,
    get_demografia,
    get_diagnosticos,
    get_prevalencia,
    get_rendimiento,
    get_resumen,
)

router = APIRouter(prefix="/analitica", tags=["analitica"])

_doctora = Depends(require_role("doctora"))


@router.get("/resumen/", response_model=ResumenKPIsResponse)
def resumen_kpis(
    sede_id: UUID | None = None,
    user=_doctora,
):
    return get_resumen(user, sede_id)


@router.get("/diagnosticos/", response_model=list[DiagnosticoRankedResponse])
def top_diagnosticos(
    sede_id: UUID | None = None,
    meses: int | None = None,
    user=_doctora,
):
    return get_diagnosticos(user, sede_id, meses)


@router.get("/demografia/", response_model=list[DemografiaGrupoResponse])
def demografia(
    sede_id: UUID | None = None,
    user=_doctora,
):
    return get_demografia(user, sede_id)


@router.get("/prevalencia/", response_model=list[PrevalenciaPuntoResponse])
def prevalencia(
    sede_id: UUID | None = None,
    patologia: str | None = None,
    meses: int | None = None,
    user=_doctora,
):
    rows = get_prevalencia(user, sede_id, patologia, meses)
    # Serialize datetime month to ISO string
    return [
        {
            "mes": (
                r["mes"].date().isoformat()
                if hasattr(r["mes"], "date")
                else str(r["mes"])
            ),
            "codigo_cie10": r["codigo_cie10"],
            "descripcion": r["descripcion"],
            "frecuencia": r["frecuencia"],
        }
        for r in rows
    ]


@router.get("/rendimiento/", response_model=list[RendimientoTipoResponse])
def rendimiento(
    sede_id: UUID | None = None,
    meses: int | None = None,
    user=_doctora,
):
    return get_rendimiento(user, sede_id, meses)


@router.get("/exportar/", response_class=PlainTextResponse)
def exportar(
    tipo: str,
    sede_id: UUID | None = None,
    meses: int | None = None,
    user=_doctora,
):
    csv_data = exportar_csv(user, tipo, sede_id, meses)
    return PlainTextResponse(
        content=csv_data,
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{tipo}.csv"',
        },
    )
