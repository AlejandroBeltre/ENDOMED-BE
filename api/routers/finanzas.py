from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends

from api.dependencies import get_current_user, require_role
from api.schemas.finanzas import (
    CajaResponse,
    EstadoFacturaRequest,
    FacturaCreateRequest,
    FacturaResponse,
    InventarioCreateRequest,
    InventarioResponse,
    InventarioUpdateRequest,
    MovimientoCreateRequest,
    MovimientoResponse,
    PagoCreateRequest,
    PagoResponse,
    ReportesResponse,
)
from apps.finanzas.services import (
    create_factura,
    create_inventario,
    create_movimiento_inventario,
    create_pago,
    get_caja_hoy,
    get_factura,
    get_reportes,
    list_facturas,
    list_inventario,
    update_factura_estado,
    update_inventario,
)

router = APIRouter(prefix="/finanzas", tags=["finanzas"])


@router.get("/caja/", response_model=CajaResponse)
def caja_hoy(
    sede_id: UUID | None = None,
    user=Depends(get_current_user),
):
    return get_caja_hoy(user, sede_id)


@router.get("/facturas/", response_model=list[FacturaResponse])
def list_facturas_route(
    sede_id: UUID | None = None,
    estado: str | None = None,
    fecha_desde: date | None = None,
    fecha_hasta: date | None = None,
    user=Depends(get_current_user),
):
    return list_facturas(user, sede_id, estado, fecha_desde, fecha_hasta)


@router.post("/facturas/", response_model=FacturaResponse, status_code=201)
def create_factura_route(
    body: FacturaCreateRequest,
    user=Depends(require_role("doctora", "secretaria")),
):
    return create_factura(body.model_dump(), user)


@router.get("/facturas/{factura_id}/", response_model=FacturaResponse)
def get_factura_route(
    factura_id: UUID,
    user=Depends(get_current_user),
):
    return get_factura(factura_id, user)


@router.patch("/facturas/{factura_id}/estado/", response_model=FacturaResponse)
def update_estado_route(
    factura_id: UUID,
    body: EstadoFacturaRequest,
    user=Depends(require_role("doctora")),
):
    return update_factura_estado(factura_id, body.estado, user)


@router.post("/pagos/", response_model=PagoResponse, status_code=201)
def create_pago_route(
    body: PagoCreateRequest,
    user=Depends(require_role("doctora", "secretaria")),
):
    return create_pago(body.model_dump(), user)


@router.get("/inventario/", response_model=list[InventarioResponse])
def list_inventario_route(user=Depends(require_role("doctora"))):
    return list_inventario(user)


@router.post("/inventario/", response_model=InventarioResponse, status_code=201)
def create_inventario_route(
    body: InventarioCreateRequest,
    user=Depends(require_role("doctora")),
):
    return create_inventario(body.model_dump(), user)


@router.patch("/inventario/{item_id}/", response_model=InventarioResponse)
def update_inventario_route(
    item_id: UUID,
    body: InventarioUpdateRequest,
    user=Depends(require_role("doctora")),
):
    return update_inventario(item_id, body.model_dump(exclude_none=True), user)


@router.post(
    "/inventario/{item_id}/movimiento/",
    response_model=MovimientoResponse,
    status_code=201,
)
def create_movimiento_route(
    item_id: UUID,
    body: MovimientoCreateRequest,
    user=Depends(require_role("doctora")),
):
    return create_movimiento_inventario(item_id, body.model_dump(), user)


@router.get("/reportes/", response_model=ReportesResponse)
def get_reportes_route(
    sede_id: UUID | None = None,
    fecha_desde: date | None = None,
    fecha_hasta: date | None = None,
    user=Depends(require_role("doctora")),
):
    return get_reportes(user, sede_id, fecha_desde, fecha_hasta)
