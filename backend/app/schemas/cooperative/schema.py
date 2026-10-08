from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class CooperativeUserRead(BaseModel):
    id: int
    name: str
    first_name: str | None = None
    email: str
    telephone: str | None = None
    address: str | None = None

    model_config = ConfigDict(from_attributes=True)


class CooperativeGareRead(BaseModel):
    id: int
    nom: str
    ville: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)

class CooperativeCreate(BaseModel):
    nom: str = Field(min_length=1, max_length=150)
    sigle: str | None = Field(default=None, max_length=50)
    numero_agrement: str | None = Field(default=None, max_length=100)
    adresse: str | None = Field(default=None, max_length=255)
    ville: str | None = Field(default=None, max_length=100)
    telephone: str | None = Field(default=None, max_length=30)
    email: str | None = Field(default=None, max_length=150)
    description: str | None = None
    responsable_id: int | None = None

class CooperativeUpdate(BaseModel):
    nom: str | None = Field(default=None, max_length=150)
    sigle: str | None = Field(default=None, max_length=50)
    numero_agrement: str | None = Field(default=None, max_length=100)
    adresse: str | None = Field(default=None, max_length=255)
    ville: str | None = Field(default=None, max_length=100)
    telephone: str | None = Field(default=None, max_length=30)
    email: str | None = Field(default=None, max_length=150)
    description: str | None = None
    responsable_id: int | None = None
    is_active: bool | None = None

class CooperativeRead(CooperativeCreate):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime | None = None
    responsable: CooperativeUserRead | None = None

    model_config = ConfigDict(from_attributes=True)

class AssociationCreate(BaseModel):
    id_cooperative: int | None = None
    date_debut: date | None = None
    date_fin: date | None = None
    is_active: bool = True


class AssociationUpdate(BaseModel):
    date_debut: date | None = None
    date_fin: date | None = None
    is_active: bool | None = None

    @model_validator(mode="after")
    def validate_dates(self):
        if self.date_debut and self.date_fin and self.date_fin < self.date_debut:
            raise ValueError("La date de fin doit être postérieure ou égale à la date de début.")
        return self


class GareCooperativeRead(BaseModel):
    id_gare: int
    id_cooperative: int
    date_debut: date | None = None
    date_fin: date | None = None
    is_active: bool
    created_at: datetime
    gare: CooperativeGareRead | None = None

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
    user: CooperativeUserRead | None = None

    model_config = ConfigDict(from_attributes=True)
