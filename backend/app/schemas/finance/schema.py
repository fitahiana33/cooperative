from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _payment_phone(value: str) -> str:
    value = value.strip()
    digits = "".join(character for character in value if character.isdigit())
    valid_local = len(digits) == 10 and digits.startswith("0")
    valid_international = len(digits) == 12 and digits.startswith("261")
    if not (valid_local or valid_international):
        raise ValueError("Renseignez un numéro malgache valide (ex. 034 00 000 00).")
    return value


class PaiementCreate(BaseModel):
    id_reservation: int
    id_caisse: int
    montant: Decimal = Field(gt=0)
    reference_paiement: str | None = Field(default=None, max_length=100)


class PaiementRead(BaseModel):
    id: int
    id_reservation: int
    numero_reservation: str | None = None
    montant: Decimal
    methode: str
    reference_paiement: str | None = None
    statut: str
    date_validation: datetime | None = None
    date_remboursement: datetime | None = None
    verification_requise: bool = False
    methode_remboursement: str | None = None
    reference_remboursement: str | None = None
    date_paiement: datetime
    id_agent: int | None = None
    remboursement_demande_le: datetime | None = None
    fournisseur: str | None = None
    reference_fournisseur: str | None = None
    cle_idempotence: str | None = None
    webhook_recu_le: datetime | None = None
    model_config = ConfigDict(from_attributes=True)


class PaiementEnLigneCreate(BaseModel):
    id_reservation: int
    montant: Decimal = Field(gt=0)
    cle_idempotence: str = Field(min_length=8, max_length=100)
    fournisseur: str = Field(default="MVOLA", pattern="^(MVOLA|ORANGE_MONEY|AIRTEL_MONEY)$")
    telephone_paiement: str = Field(min_length=10, max_length=30)

    _validate_phone = field_validator("telephone_paiement")(_payment_phone)


class PublicPaymentCreate(BaseModel):
    montant: Decimal = Field(gt=0)
    cle_idempotence: str = Field(min_length=20, max_length=100)
    fournisseur: str = Field(default="MVOLA", pattern="^(MVOLA|ORANGE_MONEY|AIRTEL_MONEY)$")
    telephone_paiement: str = Field(min_length=10, max_length=30)

    _validate_phone = field_validator("telephone_paiement")(_payment_phone)


class RefundCreate(BaseModel):
    methode: str = Field(default="ESPECES", pattern="^(ESPECES|MOBILE_MONEY|VIREMENT|CARTE)$")
    reference: str | None = Field(default=None, min_length=8, max_length=150)


class PaymentVerification(BaseModel):
    reference_verification: str = Field(min_length=8, max_length=150)


class PaiementEnLigneRead(BaseModel):
    verification_requise: bool = False
    id_paiement: int
    statut: str
    fournisseur: str
    reference_paiement: str
    montant: Decimal
    message: str
    checkout_url: str | None = None
    acompte_minimum: Decimal | None = None
    montant_restant: Decimal | None = None


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
    ecart_cloture: Decimal | None = None
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
    id_agent: int | None = None
    id: int
    id_caisse: int
    type_operation: str
    montant: Decimal
    id_paiement: int | None = None
    id_cooperative: int | None = None
    description: str | None = None
    date_operation: datetime
    model_config = ConfigDict(from_attributes=True)

