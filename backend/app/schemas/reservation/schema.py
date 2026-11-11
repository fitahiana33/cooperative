from datetime import date, datetime, time
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.finance import PaiementEnLigneRead
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
    nom_passager: str | None = Field(default=None, max_length=150)
    telephone_passager: str | None = Field(default=None, max_length=30)

    @field_validator("nom_passager")
    @classmethod
    def clean_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = " ".join(value.split())
        return value or None


class ReservationCreate(BaseModel):
    id_depart: int
    places: list[ReservationPlaceCreate] = Field(min_length=1, max_length=20)

    @model_validator(mode="after")
    def unique_places(self):
        ids = [place.id_depart_place for place in self.places]
        if len(ids) != len(set(ids)):
            raise ValueError("Une même place ne peut pas être sélectionnée deux fois.")
        if not any(place.nom_passager for place in self.places):
            raise ValueError("Le nom de la personne qui réserve est obligatoire.")
        return self


class PublicReservationCreate(BaseModel):
    cle_idempotence: str | None = Field(default=None, min_length=20, max_length=100)
    id_depart: int
    places: list[ReservationPlaceCreate] = Field(min_length=1, max_length=20)
    nom_reservataire: str = Field(min_length=2, max_length=150)
    telephone_reservataire: str = Field(min_length=8, max_length=30)
    email_reservataire: str | None = Field(default=None, max_length=150)
    montant_avance: Decimal = Field(gt=0)
    fournisseur: str = Field(default="MVOLA", pattern="^(MVOLA|ORANGE_MONEY|AIRTEL_MONEY)$")

    @field_validator("nom_reservataire", "telephone_reservataire")
    @classmethod
    def clean_contact(cls, value: str) -> str:
        value = " ".join(value.split())
        if len(value) < 2:
            raise ValueError("Cette information est obligatoire.")
        return value

    @field_validator("email_reservataire")
    @classmethod
    def clean_email(cls, value: str | None) -> str | None:
        return value.strip().lower() if value and value.strip() else None

    @model_validator(mode="after")
    def unique_public_places(self):
        ids = [place.id_depart_place for place in self.places]
        if len(ids) != len(set(ids)):
            raise ValueError("Une même place ne peut pas être sélectionnée deux fois.")
        return self


class ReservationUpdate(BaseModel):
    """Editable reservation data.

    Editing is deliberately explicit: the client sends the complete set of
    seats and passenger details, which lets the service validate the new seat
    allocation atomically.
    """

    id_depart: int
    places: list[ReservationPlaceCreate] = Field(min_length=1, max_length=20)

    @model_validator(mode="after")
    def unique_places(self):
        ids = [place.id_depart_place for place in self.places]
        if len(ids) != len(set(ids)):
            raise ValueError("Une même place ne peut pas être sélectionnée deux fois.")
        if not any(place.nom_passager for place in self.places):
            raise ValueError("Le nom de la personne qui réserve est obligatoire.")
        return self


class CounterSaleCreate(ReservationCreate):
    """Counter sale: book, confirm and optionally take cash in one request."""
    id_caisse: int | None = None
    reference_paiement: str | None = Field(default=None, max_length=100)


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
    qr_code_uuid: UUID
    statut: str
    model_config = ConfigDict(from_attributes=True)


class _NamedRead(BaseModel):
    id: int
    nom: str
    model_config = ConfigDict(from_attributes=True)


class _RouteRead(BaseModel):
    id: int
    destination_depart: _NamedRead | None = None
    destination_arrivee: _NamedRead | None = None
    model_config = ConfigDict(from_attributes=True)


class ReservationVehicleRead(BaseModel):
    id: int
    immatriculation: str
    nombre_places: int
    places_avant: int = 2
    places_par_rangee: int = 4
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
    itineraire: _RouteRead | None = None
    cooperative: _NamedRead | None = None
    vehicule: ReservationVehicleRead | None = None
    model_config = ConfigDict(from_attributes=True)


class ReservationRead(BaseModel):
    montant_rembourse: Decimal = Decimal("0")
    etat_paiement: str = "NON_REGLE"
    peut_annuler: bool = False
    peut_payer: bool = False
    minimum_a_payer: Decimal = Decimal("0")
    date_limite_annulation: datetime | None = None
    id: int
    numero_reservation: str
    id_depart: int
    id_user: int
    montant_total: Decimal
    montant_paye: Decimal = Decimal("0")
    montant_restant: Decimal = Decimal("0")
    montant_a_rembourser: Decimal = Decimal("0")
    statut: ReservationStatus
    date_expiration: datetime | None = None
    created_at: datetime
    updated_at: datetime | None = None
    nom_reservataire: str | None = None
    telephone_reservataire: str | None = None
    email_reservataire: str | None = None
    depart: ReservationDepartRead | None = None
    places: list[ReservationPlaceRead] = []
    model_config = ConfigDict(from_attributes=True)


class PublicReservationCreateRead(BaseModel):
    reservation: ReservationRead
    access_token: str
    payment: "PaiementEnLigneRead | None" = None
    acompte_minimum: Decimal

