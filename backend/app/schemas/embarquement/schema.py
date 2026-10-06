from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class EmbarquementControl(BaseModel):
    code: str = Field(min_length=3, max_length=100)
    date_heure: datetime | None = None


class EmbarquementRead(BaseModel):
    id: int
    id_billet: int
    id_agent: int
    date_heure_embarquement: datetime
    statut: str
    motif_refus: str | None = None
    model_config = ConfigDict(from_attributes=True)

