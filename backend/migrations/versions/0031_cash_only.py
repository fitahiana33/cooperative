"""Disable online payment permissions for the cash-only launch mode."""

import sqlalchemy as sa
from alembic import op


revision = "0031_cash_only"
down_revision = "0030_online_payments_audit"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(sa.text(
        "DELETE FROM roles_permissions "
        "WHERE id_permission IN (SELECT id_permission FROM permissions WHERE code = 'PAIEMENT_ONLINE')"
    ))
    op.execute(sa.text(
        "UPDATE permissions SET is_active = FALSE WHERE code = 'PAIEMENT_ONLINE'"
    ))


def downgrade() -> None:
    op.execute(sa.text(
        "UPDATE permissions SET is_active = TRUE WHERE code = 'PAIEMENT_ONLINE'"
    ))
