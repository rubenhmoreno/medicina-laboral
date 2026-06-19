from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class AdjuntoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    licencia_id: UUID
    nombre_original: str
    mime_type: str
    size_bytes: int
    sha256: str
    created_at: datetime


class AdjuntoDownload(BaseModel):
    url: str
    expires_in_seconds: int
