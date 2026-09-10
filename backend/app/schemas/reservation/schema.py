from datetime import date, datetime, time
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.place import DepartPlaceStatus
from app.models.reservation import ReservationStatus


class DepartPlaceRead(BaseModel):
    id: int
    id_depart: int
    numero_place: int
    statut: DepartPlaceStatus
    model_config = ConfigDict(from_attributes=True)


class DepartPlaceStatusUpdate(BaseModel):
    statut: DepartPlaceStatus


class ReservationPlaceCreate(BaseModel):
    id_depart_place: int
    nom_passager: str = Field(min_length=2, max_length=150)
    telephone_passager: str | None = Field(default=None, max_length=30)

    @field_validator("nom_passager")
    @classmethod
    def clean_name(cls, value: str) -> str:
        value = " ".join(value.split())
        if not value:
            raise ValueError("Le nom du passager est obligatoire.")
        return value


class ReservationCreate(BaseModel):
    id_depart: int
    places: list[ReservationPlaceCreate] = Field(min_length=1, max_length=20)
    date_expiration: datetime | None = None

    @model_validator(mode="after")
    def unique_places(self):
        ids = [place.id_depart_place for place in self.places]
        if len(ids) != len(set(ids)):
            raise ValueError("Une même place ne peut pas être sélectionnée deux fois.")
        return self


class ReservationStatusUpdate(BaseModel):
    statut: ReservationStatus


class ReservationPlaceRead(BaseModel):
    id: int
    id_depart_place: int
    nom_passager: str
    telephone_passager: str | None = None
    depart_place: DepartPlaceRead | None = None
    billet: "ReservationTicketRead | None" = None
    model_config = ConfigDict(from_attributes=True)


class ReservationTicketRead(BaseModel):
    id: int
    numero_billet: str
    qr_code_uuid: str
    statut: str
    model_config = ConfigDict(from_attributes=True)


class ReservationDepartRead(BaseModel):
    id: int
    id_itineraire: int
    id_cooperative: int
    id_vehicule: int
    date_depart: date
    heure_depart: time
    nombre_places: int
    places_reservees: int
    places_disponibles: int
    statut: str
    model_config = ConfigDict(from_attributes=True)


class ReservationRead(BaseModel):
    id: int
    numero_reservation: str
    id_depart: int
    id_user: int
    montant_total: Decimal
    statut: ReservationStatus
    date_expiration: datetime | None = None
    created_at: datetime
    updated_at: datetime | None = None
    depart: ReservationDepartRead | None = None
    places: list[ReservationPlaceRead] = []
    model_config = ConfigDict(from_attributes=True)

