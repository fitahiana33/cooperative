"""Seat layout per vehicle model, so seat maps match the real vehicles.

places_avant: seats beside the driver; places_par_rangee: seats per row
behind (the aisle sits in the middle of the row).
"""

import sqlalchemy as sa
from alembic import op


revision = "0029_seat_layout"
down_revision = "0028_counter_staff_sell_cancel"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("modeles", sa.Column("places_avant", sa.Integer(), nullable=False, server_default="2"))
    op.add_column("modeles", sa.Column("places_par_rangee", sa.Integer(), nullable=False, server_default="4"))
    op.create_check_constraint("ck_modele_places_avant", "modeles", "places_avant BETWEEN 0 AND 3")
    op.create_check_constraint("ck_modele_places_par_rangee", "modeles", "places_par_rangee BETWEEN 2 AND 6")


def downgrade() -> None:
    op.drop_constraint("ck_modele_places_par_rangee", "modeles")
    op.drop_constraint("ck_modele_places_avant", "modeles")
    op.drop_column("modeles", "places_par_rangee")
    op.drop_column("modeles", "places_avant")
