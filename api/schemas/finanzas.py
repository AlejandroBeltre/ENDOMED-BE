from datetime import date, datetime
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, BeforeValidator, ConfigDict, field_validator


def _resolve_manager(v):
    """Convert a Django RelatedManager to a list so Pydantic can validate it."""
    if hasattr(v, "all"):
        return list(v.all())
    return v


# ── nested ────────────────────────────────────────────────────────────────────


class PacienteBasicResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    nombre: str
    apellido: str
    cedula: str


class SedeBasicResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    nombre: str
    ciudad: str


class UserBasicResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    nombre: str
    apellido: str


# ── pago ─────────────────────────────────────────────────────────────────────


class PagoCreateRequest(BaseModel):
    factura_id: UUID
    monto_rd: Decimal
    metodo: str  # efectivo | tarjeta | transferencia | seguro
    referencia_transaccion: str = ""
    fecha_pago: date


class PagoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    factura_id: UUID
    monto_rd: Decimal
    metodo: str
    referencia_transaccion: str
    fecha_pago: date
    registrado_por: UserBasicResponse
    created_at: datetime


# ── factura ───────────────────────────────────────────────────────────────────


class FacturaCreateRequest(BaseModel):
    paciente_id: UUID
    sede_id: UUID
    cita_id: UUID | None = None
    seguro_id: UUID | None = None
    fecha: date
    subtotal_rd: Decimal
    descuento_rd: Decimal = Decimal("0")
    itbis_rd: Decimal = Decimal("0")

    @field_validator("subtotal_rd", "descuento_rd", "itbis_rd")
    @classmethod
    def must_be_non_negative(cls, v: Decimal) -> Decimal:
        if v < 0:
            raise ValueError("El monto no puede ser negativo.")
        return v


class EstadoFacturaRequest(BaseModel):
    estado: str  # borrador | emitida | pagada | anulada


class FacturaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    numero_factura: int
    paciente: PacienteBasicResponse
    sede: SedeBasicResponse
    cita_id: UUID | None
    fecha: date
    subtotal_rd: Decimal
    descuento_rd: Decimal
    itbis_rd: Decimal
    total_rd: Decimal
    estado: str
    created_by: UserBasicResponse
    created_at: datetime
    pagos: Annotated[list[PagoResponse], BeforeValidator(_resolve_manager)] = []

    @property
    def numero_factura_formateado(self) -> str:
        return f"F-{self.numero_factura:06d}"


# ── caja ─────────────────────────────────────────────────────────────────────


class CajaResponse(BaseModel):
    fecha: date
    facturas: list[FacturaResponse]
    total_general: Decimal
    total_pagado: Decimal


# ── inventario ────────────────────────────────────────────────────────────────


class InventarioCreateRequest(BaseModel):
    nombre_producto: str
    categoria: str  # suero | suplemento | insumo
    stock_actual: int = 0
    stock_minimo: int = 0
    precio_unitario_rd: Decimal
    proveedor: str = ""

    @field_validator("stock_actual", "stock_minimo")
    @classmethod
    def must_be_non_negative_int(cls, v: int) -> int:
        if v < 0:
            raise ValueError("El stock no puede ser negativo.")
        return v


class InventarioUpdateRequest(BaseModel):
    nombre_producto: str | None = None
    categoria: str | None = None
    stock_minimo: int | None = None
    precio_unitario_rd: Decimal | None = None
    proveedor: str | None = None


class InventarioResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    nombre_producto: str
    categoria: str
    stock_actual: int
    stock_minimo: int
    precio_unitario_rd: Decimal
    proveedor: str
    created_at: datetime
    updated_at: datetime

    @property
    def stock_bajo(self) -> bool:
        return self.stock_actual < self.stock_minimo


# ── movimiento inventario ─────────────────────────────────────────────────────


class MovimientoCreateRequest(BaseModel):
    tipo: str  # entrada | salida | ajuste
    cantidad: int
    motivo: str
    consulta_id: UUID | None = None

    @field_validator("cantidad")
    @classmethod
    def must_be_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("La cantidad debe ser mayor a 0.")
        return v


class MovimientoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    inventario_id: UUID
    tipo: str
    cantidad: int
    motivo: str
    consulta_id: UUID | None
    created_by: UserBasicResponse
    created_at: datetime


# ── reportes ──────────────────────────────────────────────────────────────────


class ReporteItemResponse(BaseModel):
    nombre: str
    total: Decimal


class ReportesResponse(BaseModel):
    total_general: Decimal
    por_sede: list[dict]
    por_tipo_consulta: list[dict]
    por_estado: list[dict]
