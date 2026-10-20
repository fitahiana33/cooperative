"""Allow passengers to modify their own pending reservations."""

import sqlalchemy as sa
from alembic import op


revision = "0034_passenger_res_update"
down_revision = "0033_notification_type"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(sa.text("""
        INSERT INTO roles_permissions (id_role, id_permission)
        SELECT r.id_role, p.id_permission
        FROM roles r CROSS JOIN permissions p
        WHERE r.libelle IN ('passenger', 'passager')
          AND p.code = 'RESERVATION_UPDATE'
          AND p.is_active = TRUE
          AND NOT EXISTS (
              SELECT 1 FROM roles_permissions rp
              WHERE rp.id_role = r.id_role AND rp.id_permission = p.id_permission
          )
    """))


def downgrade() -> None:
    op.execute(sa.text("""
        DELETE FROM roles_permissions
        WHERE id_permission = (SELECT id_permission FROM permissions WHERE code = 'RESERVATION_UPDATE')
          AND id_role IN (SELECT id_role FROM roles WHERE libelle IN ('passenger', 'passager'))
    """))
