from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class TipoConsultaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    nombre: str
    duracion_min: int
    tarifa_rd: Decimal
    color_hex: str


class PacienteBasicResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    nombre: str
    apellido: str
    cedula: str


class ProfesionalBasicResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    nombre: str
    apellido: str


class CitaCreateRequest(BaseModel):
    paciente_id: UUID
    sede_id: UUID
    profesional_id: UUID
    tipo_consulta_id: UUID
    fecha_hora: datetime
    duracion_min: int
    modalidad: str = "presencial"
    notas_previas: str = ""


class CitaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    paciente: PacienteBasicResponse
    sede_id: UUID
    profesional: ProfesionalBasicResponse
    tipo_consulta: TipoConsultaResponse
    fecha_hora: datetime
    duracion_min: int
    modalidad: str
    estado: str
    notas_previas: str
    created_at: datetime


class EstadoCitaRequest(BaseModel):
    estado: str  # pendiente | confirmada | cancelada | completada
