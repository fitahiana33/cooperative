from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class PermissionCreate(BaseModel):
    libelle: str = Field(min_length=2, max_length=100)
    code: str = Field(min_length=2, max_length=100)
    module: str = Field(min_length=2, max_length=100)
    description: str | None = None

class PermissionUpdate(BaseModel):
    libelle: str | None = Field(default=None, min_length=2, max_length=100)
    code: str | None = Field(default=None, min_length=2, max_length=100)
    module: str | None = Field(default=None, min_length=2, max_length=100)
    description: str | None = None
    is_active: bool | None = None

class PermissionRead(PermissionCreate):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
