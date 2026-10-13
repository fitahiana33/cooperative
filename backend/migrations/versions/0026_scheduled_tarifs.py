"""Fare versions that start in the future.

The current fare stays active until the new version's start date; the new
version waits as "scheduled" and is activated by the maintenance job.
"""

import sqlalchemy as sa
from alembic import op


revision = "0026_scheduled_tarifs"
down_revision = "0025_refunds_and_cash_close"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("tarifs", sa.Column("activation_programmee", sa.Boolean(), nullable=False, server_default=sa.false()))


def downgrade() -> None:
    op.drop_column("tarifs", "activation_programmee")
