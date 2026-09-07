from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class TarifBase(BaseModel):
    id_itineraire: int
    id_cooperative: int | None = None
    prix: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    devise: str = Field(default="MGA", min_length=3, max_length=10)
    date_debut: date | None = None
    date_fin: date | None = None

    @model_validator(mode="after")
    def validate_dates(self):
        if self.date_debut and self.date_fin and self.date_fin < self.date_debut:
            raise ValueError("La date de fin doit être postérieure ou égale à la date de début.")
        return self


class TarifCreate(TarifBase):
    pass


class TarifUpdate(BaseModel):
    id_cooperative: int | None = None
    prix: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    devise: str | None = Field(default=None, min_length=3, max_length=10)
    date_debut: date | None = None
    date_fin: date | None = None
    is_active: bool | None = None

    @model_validator(mode="after")
    def validate_dates(self):
        if self.date_debut and self.date_fin and self.date_fin < self.date_debut:
            raise ValueError("La date de fin doit être postérieure ou égale à la date de début.")
        return self


class TarifRead(TarifBase):
    id: int
    date_debut: date
    is_active: bool
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
