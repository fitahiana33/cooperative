"""Allow guest reservations and persist Papi payment-link callbacks."""

import sqlalchemy as sa
from alembic import op


revision = "0036_public_reservations_papi"
down_revision = "0035_departure_station"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("reservations", sa.Column("nom_reservataire", sa.String(length=150), nullable=True))
    op.add_column("reservations", sa.Column("telephone_reservataire", sa.String(length=30), nullable=True))
    op.add_column("reservations", sa.Column("email_reservataire", sa.String(length=150), nullable=True))
    op.add_column("reservations", sa.Column("acces_public_hash", sa.String(length=64), nullable=True))
    op.create_unique_constraint("uq_reservations_acces_public_hash", "reservations", ["acces_public_hash"])
    op.add_column("paiements", sa.Column("notification_token", sa.String(length=255), nullable=True))
    op.add_column("paiements", sa.Column("checkout_url", sa.String(length=500), nullable=True))


def downgrade() -> None:
    op.drop_column("paiements", "checkout_url")
    op.drop_column("paiements", "notification_token")
    op.drop_constraint("uq_reservations_acces_public_hash", "reservations", type_="unique")
    op.drop_column("reservations", "acces_public_hash")
    op.drop_column("reservations", "email_reservataire")
    op.drop_column("reservations", "telephone_reservataire")
    op.drop_column("reservations", "nom_reservataire")
