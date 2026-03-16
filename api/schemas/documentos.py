from uuid import UUID

from pydantic import BaseModel


class RecetaRequest(BaseModel):
    consulta_id: UUID
