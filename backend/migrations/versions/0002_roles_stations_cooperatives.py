"""Add roles, permissions, stations and cooperatives.

Revision ID: 0002_roles_stations_cooperatives
Revises: 0001_create_users
"""
from alembic import op
import sqlalchemy as sa

revision = "0002_roles_stations_cooperatives"
down_revision = "0001_create_users"
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Some development databases were initialized directly from
    # docs/db/cooperative.sql before Alembic was introduced. In that case
    # the complete Sprint 3/4 schema already exists and must not be rebuilt.
    bind = op.get_bind()
    if sa.inspect(bind).has_table("roles"):
        return
    op.create_table("roles",
        sa.Column("id_role", sa.BigInteger(), primary_key=True), sa.Column("libelle", sa.String(100), nullable=False, unique=True),
        sa.Column("description", sa.String(255)), sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_table("permissions",
        sa.Column("id_permission", sa.BigInteger(), primary_key=True), sa.Column("libelle", sa.String(100), nullable=False),
        sa.Column("description", sa.String(255)), sa.Column("code", sa.String(100), nullable=False, unique=True), sa.Column("module", sa.String(100), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_table("users_roles", sa.Column("id_user", sa.BigInteger(), sa.ForeignKey("users.id_user", ondelete="CASCADE"), primary_key=True), sa.Column("id_role", sa.BigInteger(), sa.ForeignKey("roles.id_role", ondelete="CASCADE"), primary_key=True))
    op.create_table("roles_permissions", sa.Column("id_role", sa.BigInteger(), sa.ForeignKey("roles.id_role", ondelete="CASCADE"), primary_key=True), sa.Column("id_permission", sa.BigInteger(), sa.ForeignKey("permissions.id_permission", ondelete="CASCADE"), primary_key=True))
    op.create_table("gares", sa.Column("id_gare", sa.Integer(), primary_key=True), sa.Column("nom", sa.String(150), nullable=False), sa.Column("adresse", sa.String(255), nullable=False), sa.Column("ville", sa.String(100), nullable=False), sa.Column("region", sa.String(100)), sa.Column("telephone", sa.String(30)), sa.Column("email", sa.String(150)), sa.Column("description", sa.Text()), sa.Column("latitude", sa.Numeric(10, 7)), sa.Column("longitude", sa.Numeric(10, 7)), sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_table("quais", sa.Column("id_quai", sa.Integer(), primary_key=True), sa.Column("id_gare", sa.Integer(), sa.ForeignKey("gares.id_gare", ondelete="CASCADE"), nullable=False), sa.Column("numero", sa.String(50), nullable=False), sa.Column("nom", sa.String(100)), sa.Column("description", sa.Text()), sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()), sa.UniqueConstraint("id_gare", "numero"))
    op.create_table("zones", sa.Column("id_zone", sa.Integer(), primary_key=True), sa.Column("id_gare", sa.Integer(), sa.ForeignKey("gares.id_gare", ondelete="CASCADE"), nullable=False), sa.Column("nom", sa.String(100), nullable=False), sa.Column("type_zone", sa.String(50)), sa.Column("description", sa.Text()), sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.create_table("emplacements", sa.Column("id_emplacement", sa.Integer(), primary_key=True), sa.Column("id_zone", sa.Integer(), sa.ForeignKey("zones.id_zone", ondelete="CASCADE"), nullable=False), sa.Column("code", sa.String(50), nullable=False), sa.Column("nom", sa.String(100)), sa.Column("type_emplacement", sa.String(50)), sa.Column("description", sa.Text()), sa.Column("is_available", sa.Boolean(), nullable=False, server_default=sa.true()), sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()), sa.UniqueConstraint("id_zone", "code"))
    op.create_table("cooperatives", sa.Column("id_cooperative", sa.Integer(), primary_key=True), sa.Column("nom", sa.String(150), nullable=False), sa.Column("sigle", sa.String(50)), sa.Column("numero_agrement", sa.String(100)), sa.Column("adresse", sa.String(255)), sa.Column("ville", sa.String(100)), sa.Column("telephone", sa.String(30)), sa.Column("email", sa.String(150)), sa.Column("description", sa.Text()), sa.Column("responsable_id", sa.Integer(), sa.ForeignKey("users.id_user", ondelete="SET NULL")), sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_table("gare_cooperatives", sa.Column("id_gare", sa.Integer(), sa.ForeignKey("gares.id_gare", ondelete="CASCADE"), primary_key=True), sa.Column("id_cooperative", sa.Integer(), sa.ForeignKey("cooperatives.id_cooperative", ondelete="CASCADE"), primary_key=True), sa.Column("date_debut", sa.Date()), sa.Column("date_fin", sa.Date()), sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_table("cooperative_members", sa.Column("id_cooperative", sa.Integer(), sa.ForeignKey("cooperatives.id_cooperative", ondelete="CASCADE"), primary_key=True), sa.Column("id_user", sa.Integer(), sa.ForeignKey("users.id_user", ondelete="CASCADE"), primary_key=True), sa.Column("fonction", sa.String(100)), sa.Column("date_adhesion", sa.Date()), sa.Column("date_fin", sa.Date()), sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    # Columns required by the SQL contract and mapped by SQLAlchemy models.
    op.add_column("roles", sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.add_column("permissions", sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.add_column("users_roles", sa.Column("assigned_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.add_column("roles_permissions", sa.Column("assigned_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.add_column("gares", sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    for table in ("quais", "zones", "emplacements"):
        op.add_column(table, sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
        op.add_column(table, sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.add_column("cooperatives", sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))

def downgrade() -> None:
    for table in ("cooperative_members", "gare_cooperatives", "cooperatives", "emplacements", "zones", "quais", "gares", "roles_permissions", "users_roles", "permissions", "roles"):
        op.drop_table(table)
