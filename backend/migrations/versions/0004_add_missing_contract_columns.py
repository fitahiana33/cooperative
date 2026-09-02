"""complete columns missing from legacy Sprint 3/4 databases"""
from alembic import op
import sqlalchemy as sa

revision = "0004_contract_columns"
down_revision = "0003_reconcile_legacy_users"
branch_labels = None
depends_on = None

def upgrade() -> None:
    bind = op.get_bind()
    additions = {
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
    for table, columns in additions.items():
        existing = {column["name"] for column in sa.inspect(bind).get_columns(table)}
        for name in columns:
            if name not in existing:
                op.add_column(table, sa.Column(name, sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))

def downgrade() -> None:
    bind = op.get_bind()
    additions = {
        "roles": ["updated_at"], "permissions": ["updated_at"],
        "users_roles": ["assigned_at"], "roles_permissions": ["assigned_at"],
        "gares": ["updated_at"], "quais": ["created_at", "updated_at"],
        "zones": ["created_at", "updated_at"], "emplacements": ["created_at", "updated_at"],
        "cooperatives": ["updated_at"],
    }
    for table, columns in additions.items():
        existing = {column["name"] for column in sa.inspect(bind).get_columns(table)}
        for name in columns:
            if name in existing:
                op.drop_column(table, name)
