from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class MarqueCreate(BaseModel):
    nom: str = Field(min_length=1, max_length=100)
    description: str | None = None

class MarqueUpdate(BaseModel):
    nom: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = None
    is_active: bool | None = None

class MarqueRead(MarqueCreate):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
