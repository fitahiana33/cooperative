"""reconcile the first development users schema with the SQL contract"""
from alembic import op
import sqlalchemy as sa

revision = "0003_reconcile_legacy_users"
down_revision = "0002_roles_stations_cooperatives"
branch_labels = None
depends_on = None

def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("users")}
    if "address" in columns and "adresse" not in columns:
        op.alter_column("users", "address", new_column_name="adresse")
    if "password_hash" in columns and "password" not in columns:
        op.alter_column("users", "password_hash", new_column_name="password")
    if "role" in columns:
        op.drop_column("users", "role")

    # Databases created by the first 0002 migration already had these tables,
    # so 0002 returned early and could not add the SQL contract timestamps.
    timestamp_columns = {
        "roles": ["updated_at"],
        "permissions": ["updated_at"],
        "users_roles": ["assigned_at"],
        "roles_permissions": ["assigned_at"],
        "gares": ["updated_at"],
        "quais": ["created_at", "updated_at"],
        "zones": ["created_at", "updated_at"],
        "emplacements": ["created_at", "updated_at"],
        "cooperatives": ["updated_at"],
    }
    for table, names in timestamp_columns.items():
        existing = {column["name"] for column in sa.inspect(bind).get_columns(table)}
        for name in names:
            if name not in existing:
                op.add_column(table, sa.Column(name, sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))

def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns("users")}
    if "password" in columns and "password_hash" not in columns:
        op.alter_column("users", "password", new_column_name="password_hash")
    if "adresse" in columns and "address" not in columns:
        op.alter_column("users", "adresse", new_column_name="address")
