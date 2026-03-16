from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class MedicamentoCreateRequest(BaseModel):
    nombre: str
    presentacion: str
    dosis: str
    frecuencia: str
    duracion: str
    indicaciones: str = ""


class MedicamentoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    nombre: str
    presentacion: str
    dosis: str
    frecuencia: str
    duracion: str
    indicaciones: str


class SignosVitalesRequest(BaseModel):
    peso_kg: Decimal | None = None
    talla_cm: Decimal | None = None
    pa_sistolica: int | None = None
    pa_diastolica: int | None = None
    fc: int | None = None
    temperatura: Decimal | None = None
    saturacion_o2: int | None = None


class SignosVitalesResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    peso_kg: Decimal | None
    talla_cm: Decimal | None
    imc: Decimal | None
    pa_sistolica: int | None
    pa_diastolica: int | None
    fc: int | None
    temperatura: Decimal | None
    saturacion_o2: int | None


class ConsultaCreateRequest(BaseModel):
    paciente_id: UUID
    cita_id: UUID | None = None
    tipo_consulta_id: UUID
    fecha_hora: datetime
    motivo_consulta: str
    examen_fisico: dict = {}
    plan_terapeutico: str = ""
    modalidad: str = "presencial"
    signos_vitales: SignosVitalesRequest | None = None
    medicamentos: list[MedicamentoCreateRequest] = []


class ConsultaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tipo_consulta_id: UUID
    fecha_hora: datetime
    motivo_consulta: str
    examen_fisico: dict
    plan_terapeutico: str
    modalidad: str
    signos_vitales: SignosVitalesResponse | None
    medicamentos: list[MedicamentoResponse]
    created_at: datetime


class HCEResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    paciente_id: UUID
    consultas: list[ConsultaResponse]
    created_at: datetime
