"""Allow a validated advance followed by collection of the remaining balance."""

from alembic import op
import sqlalchemy as sa

revision = "0037_payment_installments"
down_revision = "0036_public_reservations_papi"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # A reservation can have several receipts (advance, balance). The service
    # locks the reservation and checks the sum before accepting a new receipt.
    op.drop_index("uq_paiement_valide_reservation", table_name="paiements")


def downgrade() -> None:
    # Downgrade must fail rather than erase receipts if installments exist.
    op.create_index("uq_paiement_valide_reservation", "paiements", ["id_reservation"], unique=True,
                    postgresql_where=sa.text("statut = 'VALIDE'"))
