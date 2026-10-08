from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class QuaiCreate(BaseModel):
    numero: str = Field(min_length=1, max_length=50)
    nom: str | None = Field(default=None, max_length=100)
    description: str | None = None

class QuaiUpdate(BaseModel):
    numero: str | None = Field(default=None, max_length=50)
    nom: str | None = Field(default=None, max_length=100)
    description: str | None = None
    is_active: bool | None = None

class QuaiRead(QuaiCreate):
    id: int
    id_gare: int
    is_active: bool
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)

class EmplacementCreate(BaseModel):
    code: str = Field(min_length=1, max_length=50)
    nom: str | None = Field(default=None, max_length=100)
    type_emplacement: str | None = Field(default=None, max_length=50)
    description: str | None = None

class EmplacementRead(EmplacementCreate):
    id: int
    id_zone: int
    is_available: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)

class ZoneCreate(BaseModel):
    nom: str = Field(min_length=1, max_length=100)
    type_zone: str | None = Field(default=None, max_length=50)
    description: str | None = None

class ZoneUpdate(BaseModel):
    nom: str | None = Field(default=None, max_length=100)
    type_zone: str | None = Field(default=None, max_length=50)
    description: str | None = None
    is_active: bool | None = None

class ZoneRead(ZoneCreate):
    id: int
    id_gare: int
    is_active: bool
    created_at: datetime
    updated_at: datetime | None = None
    emplacements: list[EmplacementRead] = []

    model_config = ConfigDict(from_attributes=True)

class GareCreate(BaseModel):
    nom: str = Field(min_length=1, max_length=150)
    adresse: str = Field(min_length=1, max_length=255)
    ville: str = Field(min_length=1, max_length=100)
    region: str | None = Field(default=None, max_length=100)
    telephone: str | None = Field(default=None, max_length=30)
    email: str | None = Field(default=None, max_length=150)
    description: str | None = None
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)

class GareUpdate(BaseModel):
    nom: str | None = Field(default=None, max_length=150)
    adresse: str | None = Field(default=None, max_length=255)
    ville: str | None = Field(default=None, max_length=100)
    region: str | None = Field(default=None, max_length=100)
    telephone: str | None = Field(default=None, max_length=30)
    email: str | None = Field(default=None, max_length=150)
    description: str | None = None
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    is_active: bool | None = None

class EmplacementUpdate(BaseModel):
    code: str | None = Field(default=None, max_length=50)
    nom: str | None = Field(default=None, max_length=100)
    type_emplacement: str | None = Field(default=None, max_length=50)
    description: str | None = None
    is_available: bool | None = None
    is_active: bool | None = None

class GareRead(GareCreate):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime | None = None
    quais: list[QuaiRead] = []
    zones: list[ZoneRead] = []

    model_config = ConfigDict(from_attributes=True)


class GareAgentRead(BaseModel):
    """A station agent, with only the fields needed to manage the assignment."""
    id: int
    name: str
    first_name: str | None = None
    email: str
    telephone: str | None = None

    model_config = ConfigDict(from_attributes=True)
