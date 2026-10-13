"""Station staff sell and cancel reservations at the counter.

Station managers and agents could confirm and take payments but not create
or cancel a reservation, so counter sales and counter cancellations were
impossible. Existing databases get the two permissions here; new databases
get them from the seed.
"""

import sqlalchemy as sa
from alembic import op


revision = "0028_counter_staff_sell_cancel"
down_revision = "0027_password_changed_at"
branch_labels = None
depends_on = None

ROLES = "('responsable_gare', 'agent_gare')"
CODES = "('RESERVATION_CREATE', 'RESERVATION_CANCEL')"


def upgrade() -> None:
    op.execute(sa.text(f"""
        INSERT INTO roles_permissions (id_role, id_permission)
        SELECT r.id_role, p.id_permission FROM roles r, permissions p
        WHERE lower(r.libelle) IN {ROLES} AND p.code IN {CODES}
        ON CONFLICT DO NOTHING
    """))


def downgrade() -> None:
    op.execute(sa.text(f"""
        DELETE FROM roles_permissions rp USING roles r, permissions p
        WHERE rp.id_role = r.id_role AND rp.id_permission = p.id_permission
          AND lower(r.libelle) IN {ROLES} AND p.code IN {CODES}
    """))
