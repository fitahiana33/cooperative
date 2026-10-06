from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class PaiementCreate(BaseModel):
    id_reservation: int
    id_caisse: int
    montant: Decimal = Field(gt=0)
    reference_paiement: str | None = Field(default=None, max_length=100)


class PaiementRead(BaseModel):
    id: int
    id_reservation: int
    montant: Decimal
    methode: str
    reference_paiement: str | None = None
    statut: str
    date_paiement: datetime
    id_agent: int | None = None
    model_config = ConfigDict(from_attributes=True)


class CaisseOpen(BaseModel):
    id_gare: int
    montant_ouverture: Decimal = Field(default=0, ge=0)


class CaisseClose(BaseModel):
    montant_cloture: Decimal | None = Field(default=None, ge=0)


class CaisseRead(BaseModel):
    id: int
    id_gare: int
    id_agent: int
    date_ouverture: datetime
    montant_ouverture: Decimal
    date_cloture: datetime | None = None
    montant_cloture: Decimal | None = None
    statut: str
    total_recettes: Decimal = Decimal("0")
    total_depenses: Decimal = Decimal("0")
    total_commissions: Decimal = Decimal("0")
    solde: Decimal = Decimal("0")
    model_config = ConfigDict(from_attributes=True)


class OperationCreate(BaseModel):
    type_operation: str
    montant: Decimal = Field(gt=0)
    id_cooperative: int | None = None
    description: str | None = Field(default=None, max_length=255)


class OperationRead(BaseModel):
    id: int
    id_caisse: int
    type_operation: str
    montant: Decimal
    id_paiement: int | None = None
    id_cooperative: int | None = None
    description: str | None = None
    date_operation: datetime
    model_config = ConfigDict(from_attributes=True)

