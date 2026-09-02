"""complete user audit timestamps in legacy databases"""
from alembic import op
import sqlalchemy as sa

revision = "0005_user_timestamps"
down_revision = "0004_contract_columns"
branch_labels = None
depends_on = None

def upgrade() -> None:
    bind = op.get_bind()
    existing = {column["name"] for column in sa.inspect(bind).get_columns("users")}
    for name in ("last_login_at", "updated_at"):
        if name not in existing:
            op.add_column("users", sa.Column(name, sa.DateTime(timezone=True), server_default=sa.func.now() if name == "updated_at" else None, nullable=name != "updated_at"))

def downgrade() -> None:
    bind = op.get_bind()
    existing = {column["name"] for column in sa.inspect(bind).get_columns("users")}
    for name in ("last_login_at", "updated_at"):
        if name in existing:
            op.drop_column("users", name)
