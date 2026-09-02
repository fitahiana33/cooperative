"""Persist JWT revocation so logout invalidates access and refresh tokens."""

from alembic import op
import sqlalchemy as sa


revision = "0008_revoked_tokens"
down_revision = "0007_fleet"
branch_labels = None
depends_on = None


def upgrade() -> None:
    if not sa.inspect(op.get_bind()).has_table("revoked_tokens"):
        op.create_table(
            "revoked_tokens",
            sa.Column("jti", sa.String(64), primary_key=True),
            sa.Column("token_type", sa.String(20), nullable=False),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        )
        op.create_index("idx_revoked_tokens_expires_at", "revoked_tokens", ["expires_at"])


def downgrade() -> None:
    if sa.inspect(op.get_bind()).has_table("revoked_tokens"):
        op.drop_index("idx_revoked_tokens_expires_at", table_name="revoked_tokens")
        op.drop_table("revoked_tokens")
