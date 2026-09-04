"""Align the legacy PostgreSQL schema with cooperative.sql and ORM metadata."""

from alembic import op
import sqlalchemy as sa


revision = "0012_align_postgresql_contract"
down_revision = "0011_unique_vehicle_assignment"
branch_labels = None
depends_on = None


_FK_TABLES = (
    "users_roles",
    "roles_permissions",
    "quais",
    "zones",
    "emplacements",
    "cooperatives",
    "gare_cooperatives",
    "cooperative_members",
    "modeles",
    "vehicules",
    "vehicule_documents",
    "chauffeurs",
    "vehicule_chauffeurs",
)


def _drop_foreign_keys(bind) -> list[dict[str, str]]:
    rows = bind.execute(
        sa.text(
            """
            SELECT c.conname AS constraint_name, child.relname AS table_name
            FROM pg_constraint c
            JOIN pg_class child ON child.oid = c.conrelid
            JOIN pg_namespace n ON n.oid = child.relnamespace
            WHERE c.contype = 'f'
              AND n.nspname = current_schema()
              AND child.relname = ANY(:tables)
            """
        ),
        {"tables": list(_FK_TABLES)},
    ).mappings().all()
    for row in rows:
        op.drop_constraint(row["constraint_name"], row["table_name"], type_="foreignkey")
    return [dict(row) for row in rows]


def _alter_integer_to_bigint(bind, table_name: str, column_name: str) -> None:
    column = next(
        item for item in sa.inspect(bind).get_columns(table_name)
        if item["name"] == column_name
    )
    if str(column["type"]).upper() == "INTEGER":
        op.alter_column(
            table_name,
            column_name,
            type_=sa.BigInteger(),
            existing_type=sa.Integer(),
            postgresql_using=f"{column_name}::bigint",
        )


def _create_indexes() -> None:
    indexes = {
        "idx_users_email": ("users", "email"),
        "idx_users_telephone": ("users", "telephone"),
        "idx_users_roles_user": ("users_roles", "id_user"),
        "idx_users_roles_role": ("users_roles", "id_role"),
        "idx_roles_permissions_role": ("roles_permissions", "id_role"),
        "idx_roles_permissions_permission": ("roles_permissions", "id_permission"),
        "idx_quais_gare": ("quais", "id_gare"),
        "idx_zones_gare": ("zones", "id_gare"),
        "idx_emplacements_zone": ("emplacements", "id_zone"),
        "idx_cooperative_responsable": ("cooperatives", "responsable_id"),
        "idx_gare_cooperatives_gare": ("gare_cooperatives", "id_gare"),
        "idx_gare_cooperatives_cooperative": ("gare_cooperatives", "id_cooperative"),
        "idx_cooperative_members_user": ("cooperative_members", "id_user"),
        "idx_cooperative_members_cooperative": ("cooperative_members", "id_cooperative"),
        "idx_modeles_marque": ("modeles", "id_marque"),
        "idx_vehicules_modele": ("vehicules", "id_modele"),
        "idx_vehicules_cooperative": ("vehicules", "id_cooperative"),
        "idx_vehicules_immatriculation": ("vehicules", "immatriculation"),
        "idx_vehicules_disponibilite": ("vehicules", "disponibilite"),
        "idx_vehicules_etat": ("vehicules", "etat"),
        "idx_vehicule_documents_vehicule": ("vehicule_documents", "id_vehicule"),
        "idx_vehicule_documents_type": ("vehicule_documents", "type_document"),
        "idx_vehicule_documents_expiration": ("vehicule_documents", "date_expiration"),
        "idx_chauffeurs_user": ("chauffeurs", "id_user"),
        "idx_chauffeurs_cooperative": ("chauffeurs", "id_cooperative"),
        "idx_chauffeurs_disponibilite": ("chauffeurs", "disponibilite"),
        "idx_chauffeurs_expiration_permis": ("chauffeurs", "date_expiration_permis"),
        "idx_vehicule_chauffeurs_vehicule": ("vehicule_chauffeurs", "id_vehicule"),
        "idx_vehicule_chauffeurs_chauffeur": ("vehicule_chauffeurs", "id_chauffeur"),
        "idx_vehicule_chauffeurs_active": ("vehicule_chauffeurs", "is_active"),
    }
    for index_name, (table_name, column_name) in indexes.items():
        op.execute(
            sa.text(
                f'CREATE INDEX IF NOT EXISTS "{index_name}" '
                f'ON "{table_name}" ("{column_name}")'
            )
        )


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table("users"):
        return

    _drop_foreign_keys(bind)

    for table_name, columns in {
        "users": ("id_user",),
        "roles": ("id_role",),
        "permissions": ("id_permission",),
        "users_roles": ("id_user", "id_role"),
        "roles_permissions": ("id_role", "id_permission"),
        "gares": ("id_gare",),
        "quais": ("id_quai", "id_gare"),
        "zones": ("id_zone", "id_gare"),
        "emplacements": ("id_emplacement", "id_zone"),
        "cooperatives": ("id_cooperative", "responsable_id"),
        "gare_cooperatives": ("id_gare", "id_cooperative"),
        "cooperative_members": ("id_cooperative", "id_user"),
    }.items():
        for column_name in columns:
            _alter_integer_to_bigint(bind, table_name, column_name)

    op.alter_column("users", "first_name", nullable=True, existing_type=sa.String(100))
    op.alter_column(
        "users",
        "email",
        type_=sa.String(150),
        existing_type=sa.String(255),
        existing_nullable=False,
    )

    current_constraints = sa.inspect(bind).get_check_constraints("vehicule_documents")
    if any(item.get("name") == "ck_vehicule_document_type" for item in current_constraints):
        op.drop_constraint("ck_vehicule_document_type", "vehicule_documents", type_="check")
    op.create_check_constraint(
        "ck_vehicule_document_type",
        "vehicule_documents",
        "type_document IN ('CARTE_GRISE', 'ASSURANCE', 'VISITE_TECHNIQUE', 'AUTRE_DOCUMENT')",
    )

    foreign_keys = (
        ("users_roles", "fk_users_roles_user", "users", ["id_user"], ["id_user"]),
        ("users_roles", "fk_users_roles_role", "roles", ["id_role"], ["id_role"]),
        ("roles_permissions", "fk_roles_permissions_role", "roles", ["id_role"], ["id_role"]),
        ("roles_permissions", "fk_roles_permissions_permission", "permissions", ["id_permission"], ["id_permission"]),
        ("quais", "fk_quais_gare", "gares", ["id_gare"], ["id_gare"]),
        ("zones", "fk_zones_gare", "gares", ["id_gare"], ["id_gare"]),
        ("emplacements", "fk_emplacements_zone", "zones", ["id_zone"], ["id_zone"]),
        ("cooperatives", "fk_cooperative_responsable", "users", ["responsable_id"], ["id_user"]),
        ("gare_cooperatives", "fk_gare_cooperatives_gare", "gares", ["id_gare"], ["id_gare"]),
        ("gare_cooperatives", "fk_gare_cooperatives_cooperative", "cooperatives", ["id_cooperative"], ["id_cooperative"]),
        ("cooperative_members", "fk_cooperative_members_cooperative", "cooperatives", ["id_cooperative"], ["id_cooperative"]),
        ("cooperative_members", "fk_cooperative_members_user", "users", ["id_user"], ["id_user"]),
        ("modeles", "fk_modeles_marque", "marques", ["id_marque"], ["id_marque"]),
        ("vehicules", "fk_vehicule_modele", "modeles", ["id_modele"], ["id_modele"]),
        ("vehicules", "fk_vehicule_proprietaire", "cooperatives", ["id_cooperative"], ["id_cooperative"]),
        ("vehicule_documents", "fk_vehicule_document_vehicule", "vehicules", ["id_vehicule"], ["id_vehicule"]),
        ("chauffeurs", "fk_chauffeur_user", "users", ["id_user"], ["id_user"]),
        ("chauffeurs", "fk_chauffeur_cooperative", "cooperatives", ["id_cooperative"], ["id_cooperative"]),
        ("vehicule_chauffeurs", "fk_vehicule_chauffeurs_vehicule", "vehicules", ["id_vehicule"], ["id_vehicule"]),
        ("vehicule_chauffeurs", "fk_vehicule_chauffeurs_chauffeur", "chauffeurs", ["id_chauffeur"], ["id_chauffeur"]),
    )
    for table, name, referred_table, local_cols, remote_cols in foreign_keys:
        op.create_foreign_key(name, table, referred_table, local_cols, remote_cols, ondelete="CASCADE" if table in {"users_roles", "roles_permissions", "gare_cooperatives", "cooperative_members", "vehicule_documents", "vehicule_chauffeurs"} else ("SET NULL" if name == "fk_cooperative_responsable" else "RESTRICT"))

    _create_indexes()


def downgrade() -> None:
    # The migration only makes PostgreSQL more compatible with the canonical
    # schema. Reversing INTEGER/BIGINT safely would require a data migration.
    pass
