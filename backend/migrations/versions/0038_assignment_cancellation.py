"""Distinguish a future assignment from a manually cancelled assignment."""

from alembic import op
import sqlalchemy as sa

revision = "0038_assignment_cancellation"
down_revision = "0037_payment_installments"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("vehicule_chauffeurs", sa.Column("is_cancelled", sa.Boolean(), nullable=False, server_default=sa.false()))
    # Preserve closed rows. Future inactive rows remain eligible for planning.
    op.execute("UPDATE vehicule_chauffeurs SET is_cancelled = TRUE WHERE is_active = FALSE AND date_fin IS NOT NULL AND date_fin <= CURRENT_DATE")


def downgrade() -> None:
    op.drop_column("vehicule_chauffeurs", "is_cancelled")
