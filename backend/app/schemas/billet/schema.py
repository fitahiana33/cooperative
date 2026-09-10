from datetime import date, datetime, time
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class BilletRead(BaseModel):
    id: int
    numero_billet: str
    id_reservation_place: int
    qr_code_uuid: str
    qr_code_path: str | None = None
    statut: str
    date_emission: datetime
    date_utilisation: datetime | None = None
    reservation_id: int | None = None
    numero_reservation: str | None = None
    id_user: int | None = None
    nom_passager: str | None = None
    telephone_passager: str | None = None
    numero_place: int | None = None
    id_depart: int | None = None
    date_depart: date | None = None
    heure_depart: time | None = None
    statut_depart: str | None = None
    prix: Decimal | None = None
    devise: str | None = None
    destination_depart: str | None = None
    destination_arrivee: str | None = None
    immatriculation: str | None = None
    nom_cooperative: str | None = None
    model_config = ConfigDict(from_attributes=True)

