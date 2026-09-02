from datetime import datetime
from pydantic import BaseModel, ConfigDict

class QuaiCreate(BaseModel):
    numero: str
    nom: str | None = None
    description: str | None = None

class QuaiUpdate(BaseModel):
    numero: str | None = None
    nom: str | None = None
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
    code: str
    nom: str | None = None
    type_emplacement: str | None = None
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
    nom: str
    type_zone: str | None = None
    description: str | None = None

class ZoneUpdate(BaseModel):
    nom: str | None = None
    type_zone: str | None = None
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
    nom: str
    adresse: str
    ville: str
    region: str | None = None
    telephone: str | None = None
    email: str | None = None
    description: str | None = None
    latitude: float | None = None
    longitude: float | None = None

class GareUpdate(BaseModel):
    nom: str | None = None
    adresse: str | None = None
    ville: str | None = None
    region: str | None = None
    telephone: str | None = None
    email: str | None = None
    description: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    is_active: bool | None = None

class EmplacementUpdate(BaseModel):
    code: str | None = None
    nom: str | None = None
    type_emplacement: str | None = None
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
