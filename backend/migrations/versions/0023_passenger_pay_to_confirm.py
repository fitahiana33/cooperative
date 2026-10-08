"""Passengers can no longer confirm their own reservations.

A passenger's reservation is confirmed by its payment (or by staff), so the
passenger role loses RESERVATION_UPDATE. The seed only inserts missing rows,
so existing databases are updated here.
"""

import sqlalchemy as sa
from alembic import op


revision = "0023_passenger_pay_to_confirm"
down_revision = "0022_board_all_tickets"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(sa.text("""
        DELETE FROM roles_permissions rp
        USING roles r, permissions p
        WHERE rp.id_role = r.id_role AND rp.id_permission = p.id_permission
          AND lower(r.libelle) IN ('passenger', 'passager') AND p.code = 'RESERVATION_UPDATE'
    """))


def downgrade() -> None:
    op.execute(sa.text("""
        INSERT INTO roles_permissions (id_role, id_permission)
        SELECT r.id_role, p.id_permission FROM roles r, permissions p
        WHERE lower(r.libelle) IN ('passenger', 'passager') AND p.code = 'RESERVATION_UPDATE'
        ON CONFLICT DO NOTHING
    """))
