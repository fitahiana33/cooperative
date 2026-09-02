from datetime import date, datetime
from pydantic import BaseModel, ConfigDict

class CooperativeCreate(BaseModel):
    nom: str
    sigle: str | None = None
    numero_agrement: str | None = None
    adresse: str | None = None
    ville: str | None = None
    telephone: str | None = None
    email: str | None = None
    description: str | None = None
    responsable_id: int | None = None

class CooperativeUpdate(BaseModel):
    nom: str | None = None
    sigle: str | None = None
    numero_agrement: str | None = None
    adresse: str | None = None
    ville: str | None = None
    telephone: str | None = None
    email: str | None = None
    description: str | None = None
    responsable_id: int | None = None
    is_active: bool | None = None

class CooperativeRead(CooperativeCreate):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)

class AssociationCreate(BaseModel):
    id_cooperative: int | None = None
    date_debut: date | None = None
    date_fin: date | None = None

class GareCooperativeRead(BaseModel):
    id_gare: int
    id_cooperative: int
    date_debut: date | None = None
    date_fin: date | None = None
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class MemberCreate(BaseModel):
    id_user: int
    fonction: str | None = None
    date_adhesion: date | None = None
    date_fin: date | None = None

class MemberUpdate(BaseModel):
    fonction: str | None = None
    date_adhesion: date | None = None
    date_fin: date | None = None
    is_active: bool | None = None

class CooperativeMemberRead(BaseModel):
    id_cooperative: int
    id_user: int
    fonction: str | None = None
    date_adhesion: date | None = None
    date_fin: date | None = None
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
