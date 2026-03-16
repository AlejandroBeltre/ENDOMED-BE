from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class PacienteCreateRequest(BaseModel):
    cedula: str
    nombre: str
    apellido: str
    fecha_nacimiento: date
    sexo: str  # M | F
    telefono_whatsapp: str
    email: str = ""
    sede_id: UUID


class PacienteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    cedula: str
    nombre: str
    apellido: str
    fecha_nacimiento: date
    sexo: str
    telefono_whatsapp: str
    email: str
    sede_id: UUID
    created_at: datetime
