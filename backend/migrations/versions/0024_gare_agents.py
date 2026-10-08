"""Attach station agents to their station.

Agents were scoped through cooperative membership, so a new agent saw no
departures, reservations or tickets. They are now attached to a station and
see the cooperatives that operate there.
"""

import sqlalchemy as sa
from alembic import op


revision = "0024_gare_agents"
down_revision = "0023_passenger_pay_to_confirm"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "gare_agents",
        sa.Column("id_gare", sa.BigInteger(), sa.ForeignKey("gares.id_gare", ondelete="CASCADE"), primary_key=True),
        sa.Column("id_user", sa.BigInteger(), sa.ForeignKey("users.id_user", ondelete="CASCADE"), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_gare_agents_user", "gare_agents", ["id_user"])


def downgrade() -> None:
    op.drop_index("idx_gare_agents_user", table_name="gare_agents")
    op.drop_table("gare_agents")
