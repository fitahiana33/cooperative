from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.destination import DestinationRead


class ItineraireBase(BaseModel):
    id_destination_depart: int
    id_destination_arrivee: int
    distance_km: Decimal | None = Field(default=None, gt=0, max_digits=8, decimal_places=2)
    duree_estimee_minutes: int | None = Field(default=None, gt=0)
    description: str | None = None

    @model_validator(mode="after")
    def validate_destinations(self):
        if self.id_destination_depart == self.id_destination_arrivee:
            raise ValueError("Le départ et l'arrivée doivent être différents.")
        return self


class ItineraireCreate(ItineraireBase):
    pass


class ItineraireUpdate(BaseModel):
    id_destination_depart: int | None = None
    id_destination_arrivee: int | None = None
    distance_km: Decimal | None = Field(default=None, gt=0, max_digits=8, decimal_places=2)
    duree_estimee_minutes: int | None = Field(default=None, gt=0)
    description: str | None = None
    is_active: bool | None = None

    @model_validator(mode="after")
    def validate_destinations(self):
        if (
            self.id_destination_depart is not None
            and self.id_destination_arrivee is not None
            and self.id_destination_depart == self.id_destination_arrivee
        ):
            raise ValueError("Le départ et l'arrivée doivent être différents.")
        return self


class ItineraireCooperativeCreate(BaseModel):
    date_debut: date | None = None
    date_fin: date | None = None
    is_active: bool = True

    @model_validator(mode="after")
    def validate_dates(self):
        if self.date_debut and self.date_fin and self.date_fin < self.date_debut:
            raise ValueError("La date de fin doit être postérieure ou égale à la date de début.")
        return self


class ItineraireCooperativeOwnerRead(BaseModel):
    id: int
    nom: str
    ville: str | None = None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class ItineraireCooperativeRead(BaseModel):
    id_itineraire: int
    id_cooperative: int
    date_debut: date
    date_fin: date | None = None
    is_active: bool
    created_at: datetime
    cooperative: ItineraireCooperativeOwnerRead | None = None

    model_config = ConfigDict(from_attributes=True)


class ItineraireRead(ItineraireBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime | None = None
    destination_depart: DestinationRead | None = None
    destination_arrivee: DestinationRead | None = None
    cooperatives: list[ItineraireCooperativeRead] = []

    model_config = ConfigDict(from_attributes=True)
