from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class ModeleCreate(BaseModel):
    id_marque: int
    nom: str = Field(min_length=1, max_length=100)
    description: str | None = None
    places_avant: int = Field(default=2, ge=0, le=3)
    places_par_rangee: int = Field(default=4, ge=2, le=6)

class ModeleUpdate(BaseModel):
    id_marque: int | None = None
    nom: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = None
    places_avant: int | None = Field(default=None, ge=0, le=3)
    places_par_rangee: int | None = Field(default=None, ge=2, le=6)
    is_active: bool | None = None

class ModeleMarqueRead(BaseModel):
    id: int
    nom: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)

class ModeleRead(ModeleCreate):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime | None = None
    marque: ModeleMarqueRead | None = None

    model_config = ConfigDict(from_attributes=True)
