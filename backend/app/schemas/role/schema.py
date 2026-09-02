from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class RoleCreate(BaseModel):
    libelle: str = Field(min_length=2, max_length=100)
    description: str | None = None

class RoleUpdate(BaseModel):
    libelle: str | None = Field(default=None, min_length=2, max_length=100)
    description: str | None = None
    is_active: bool | None = None

class RoleRead(RoleCreate):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
