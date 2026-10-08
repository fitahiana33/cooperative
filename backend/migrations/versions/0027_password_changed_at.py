"""Record when a password changes so older sessions can be refused."""

import sqlalchemy as sa
from alembic import op


revision = "0027_password_changed_at"
down_revision = "0026_scheduled_tarifs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("password_changed_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "password_changed_at")
