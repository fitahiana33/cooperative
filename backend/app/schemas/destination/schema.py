from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DestinationBase(BaseModel):
    nom: str = Field(min_length=1, max_length=150)
    region: str | None = Field(default=None, max_length=100)
    description: str | None = None


class DestinationCreate(DestinationBase):
    pass


class DestinationUpdate(BaseModel):
    nom: str | None = Field(default=None, min_length=1, max_length=150)
    region: str | None = Field(default=None, max_length=100)
    description: str | None = None
    is_active: bool | None = None


class DestinationRead(DestinationBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
