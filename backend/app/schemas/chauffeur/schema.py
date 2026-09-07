from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


class ChauffeurUserRead(BaseModel):
    id: int
    name: str
    first_name: str | None = None
    email: EmailStr
    telephone: str | None = None
    address: str | None = None

    model_config = ConfigDict(from_attributes=True)


class ChauffeurCooperativeRead(BaseModel):
    id: int
    nom: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class ChauffeurVehiculeRead(BaseModel):
    id: int
    id_modele: int
    immatriculation: str
    disponibilite: bool
    etat: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)

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
    permis_expire: bool
    user: ChauffeurUserRead | None = None
    cooperative: ChauffeurCooperativeRead | None = None
    vehicule_actuel: ChauffeurVehiculeRead | None = None
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)

class VehiculeChauffeurAssign(BaseModel):
    id_vehicule: int
    date_debut: date
    date_fin: date | None = None

    @model_validator(mode="after")
    def validate_period(self):
        if self.date_fin is not None and self.date_fin < self.date_debut:
            raise ValueError("La date de fin ne peut pas être antérieure à la date de début.")
        return self

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
