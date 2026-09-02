"""create users table matching docs/db/cooperative.sql"""
from alembic import op
import sqlalchemy as sa

revision = "0001_create_users"
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id_user", sa.BigInteger(), sa.Identity(always=True), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("first_name", sa.String(100)),
        sa.Column("email", sa.String(150), nullable=False),
        sa.Column("telephone", sa.String(30)),
        sa.Column("adresse", sa.String(255)),
        sa.Column("password", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("last_login_at", sa.DateTime()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("idx_users_email", "users", ["email"])
    op.create_index("idx_users_telephone", "users", ["telephone"])

def downgrade() -> None:
    op.drop_index("idx_users_telephone", table_name="users")
    op.drop_index("idx_users_email", table_name="users")
    op.drop_table("users")
