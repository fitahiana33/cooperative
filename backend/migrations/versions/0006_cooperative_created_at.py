"""add cooperative creation timestamp required by the ORM contract"""
from alembic import op
import sqlalchemy as sa

revision = "0006_coop_created_at"
down_revision = "0005_user_timestamps"
branch_labels = None
depends_on = None

def upgrade() -> None:
    columns = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("cooperatives")}
    if "created_at" not in columns:
        op.add_column("cooperatives", sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))

def downgrade() -> None:
    columns = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("cooperatives")}
    if "created_at" in columns:
        op.drop_column("cooperatives", "created_at")
