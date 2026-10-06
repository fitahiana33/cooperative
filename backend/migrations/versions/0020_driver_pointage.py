"""Add departure and arrival timestamps for driver attendance."""

import sqlalchemy as sa
from alembic import op


revision = "0020_driver_pointage"
down_revision = "0019_s8_s12_finance"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("departs", sa.Column("date_heure_depart", sa.DateTime(timezone=True), nullable=True))
    op.add_column("departs", sa.Column("date_heure_arrivee", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("departs", "date_heure_arrivee")
    op.drop_column("departs", "date_heure_depart")
