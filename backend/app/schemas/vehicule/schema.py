from datetime import date, datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

VehiculeEtat = Literal["BON_ETAT", "MOYEN", "A_REPARER", "HORS_SERVICE"]
DocumentType = Literal["CARTE_GRISE", "ASSURANCE", "VISITE_TECHNIQUE"]

class VehiculeDocumentDates(BaseModel):
    date_delivrance: date | None = None
    date_expiration: date | None = None

    @model_validator(mode="after")
    def validate_dates(self):
        if (
            self.date_delivrance is not None
            and self.date_expiration is not None
            and self.date_expiration < self.date_delivrance
        ):
            raise ValueError("La date d'expiration doit être postérieure ou égale à la date de délivrance.")
        return self


class VehiculeDocumentCreate(VehiculeDocumentDates):
    type_document: DocumentType
    numero_document: str | None = None
    fichier_path: str | None = None

class VehiculeDocumentUpdate(VehiculeDocumentDates):
    type_document: DocumentType | None = None
    numero_document: str | None = None
    fichier_path: str | None = None
    is_valid: bool | None = None
    is_active: bool | None = None

class VehiculeDocumentRead(VehiculeDocumentCreate):
    id: int
    id_vehicule: int
    is_valid: bool
    is_active: bool
    is_expired: bool
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)

class VehiculeCreate(BaseModel):
    id_modele: int
    id_cooperative: int
    immatriculation: str = Field(min_length=2, max_length=30)
    chevaux: int | None = Field(default=None, gt=0)
    nombre_places: int = Field(gt=0)
    disponibilite: bool = True
    etat: VehiculeEtat = "BON_ETAT"
    description: str | None = None

class VehiculeUpdate(BaseModel):
    id_modele: int | None = None
    id_cooperative: int | None = None
    immatriculation: str | None = Field(default=None, min_length=2, max_length=30)
    chevaux: int | None = Field(default=None, gt=0)
    nombre_places: int | None = Field(default=None, gt=0)
    disponibilite: bool | None = None
    etat: VehiculeEtat | None = None
    description: str | None = None
    is_active: bool | None = None

class VehiculeRead(VehiculeCreate):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime | None = None
    documents: list[VehiculeDocumentRead] = []

    model_config = ConfigDict(from_attributes=True)
