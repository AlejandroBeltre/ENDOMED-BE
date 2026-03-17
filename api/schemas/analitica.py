from decimal import Decimal

from pydantic import BaseModel


class ResumenKPIsResponse(BaseModel):
    total_pacientes: int
    consultas_este_mes: int
    ingresos_este_mes: Decimal
    citas_hoy: int


class DiagnosticoRankedResponse(BaseModel):
    codigo_cie10: str
    descripcion: str
    frecuencia: int


class DemografiaGrupoResponse(BaseModel):
    grupo_etario: str
    masculino: int
    femenino: int
    total: int


class PrevalenciaPuntoResponse(BaseModel):
    mes: str  # ISO date string for the month
    codigo_cie10: str
    descripcion: str
    frecuencia: int


class RendimientoTipoResponse(BaseModel):
    tipo_consulta: str
    volumen: int
    ingresos: Decimal
