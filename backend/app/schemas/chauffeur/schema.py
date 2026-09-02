from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, Field

class ChauffeurCreate(BaseModel):
    id_user: int
    id_cooperative: int
    numero_permis: str = Field(min_length=2, max_length=100)
    categorie_permis: str = Field(min_length=1, max_length=20)
    date_expiration_permis: date
    disponibilite: bool = True

class ChauffeurUpdate(BaseModel):
    id_cooperative: int | None = None
    numero_permis: str | None = Field(default=None, min_length=2, max_length=100)
    categorie_permis: str | None = Field(default=None, min_length=1, max_length=20)
    date_expiration_permis: date | None = None
    disponibilite: bool | None = None
    is_active: bool | None = None

class ChauffeurRead(ChauffeurCreate):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)

class VehiculeChauffeurAssign(BaseModel):
    id_vehicule: int
    date_debut: date
    date_fin: date | None = None

class VehiculeChauffeurClose(BaseModel):
    date_debut: date

class VehiculeChauffeurRead(BaseModel):
    id_vehicule: int
    id_chauffeur: int
    date_debut: date
    date_fin: date | None = None
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
