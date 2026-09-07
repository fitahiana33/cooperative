from datetime import date, datetime, time
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.depart import DepartStatus


DepartStatusValue = Literal[
    DepartStatus.PROGRAMME,
    DepartStatus.EMBARQUEMENT,
    DepartStatus.RETARDE,
    DepartStatus.PARTI,
    DepartStatus.TERMINE,
    DepartStatus.ANNULE,
]


class DepartCreate(BaseModel):
    id_itineraire: int
    id_cooperative: int
    id_vehicule: int
    id_chauffeur: int
    id_tarif: int
    date_depart: date
    heure_depart: time
    nombre_places: int | None = Field(default=None, gt=0)


class DepartUpdate(BaseModel):
    id_itineraire: int | None = None
    id_cooperative: int | None = None
    id_vehicule: int | None = None
    id_chauffeur: int | None = None
    id_tarif: int | None = None
    date_depart: date | None = None
    heure_depart: time | None = None
    nombre_places: int | None = Field(default=None, gt=0)


class DepartStatusUpdate(BaseModel):
    statut: DepartStatusValue


class DepartDestinationRead(BaseModel):
    id: int
    nom: str

    model_config = ConfigDict(from_attributes=True)


class DepartItineraireRead(BaseModel):
    id: int
    id_destination_depart: int
    id_destination_arrivee: int
    destination_depart: DepartDestinationRead | None = None
    destination_arrivee: DepartDestinationRead | None = None

    model_config = ConfigDict(from_attributes=True)


class DepartCooperativeRead(BaseModel):
    id: int
    nom: str

    model_config = ConfigDict(from_attributes=True)


class DepartVehiculeRead(BaseModel):
    id: int
    immatriculation: str
    nombre_places: int

    model_config = ConfigDict(from_attributes=True)


class DepartChauffeurRead(BaseModel):
    id: int
    id_user: int
    numero_permis: str

    model_config = ConfigDict(from_attributes=True)


class DepartTarifRead(BaseModel):
    id: int
    prix: Decimal
    devise: str

    model_config = ConfigDict(from_attributes=True)


class DepartRead(BaseModel):
    id: int
    id_itineraire: int
    id_cooperative: int
    id_vehicule: int
    id_chauffeur: int
    id_tarif: int
    date_depart: date
    heure_depart: time
    nombre_places: int
    places_reservees: int
    places_disponibles: int
    taux_remplissage: float
    statut: DepartStatusValue
    created_at: datetime
    updated_at: datetime | None = None
    itineraire: DepartItineraireRead | None = None
    cooperative: DepartCooperativeRead | None = None
    vehicule: DepartVehiculeRead | None = None
    chauffeur: DepartChauffeurRead | None = None
    tarif: DepartTarifRead | None = None

    model_config = ConfigDict(from_attributes=True)

