"""Protect vehicle documents and assignment history from hard deletes."""

from alembic import op


revision = "0015_restrict_fleet_history"
down_revision = "0014_restrict_station_fks"
branch_labels = None
depends_on = None


def upgrade() -> None:
    foreign_keys = (
        (
            "vehicule_documents",
            "fk_vehicule_document_vehicule",
            "vehicules",
            ["id_vehicule"],
            ["id_vehicule"],
        ),
        (
            "vehicule_chauffeurs",
            "fk_vehicule_chauffeurs_vehicule",
            "vehicules",
            ["id_vehicule"],
            ["id_vehicule"],
        ),
        (
            "vehicule_chauffeurs",
            "fk_vehicule_chauffeurs_chauffeur",
            "chauffeurs",
            ["id_chauffeur"],
            ["id_chauffeur"],
        ),
    )
    for table, constraint_name, referred_table, local_columns, remote_columns in foreign_keys:
        op.drop_constraint(constraint_name, table, type_="foreignkey")
        op.create_foreign_key(
            constraint_name,
            table,
            referred_table,
            local_columns,
            remote_columns,
            ondelete="RESTRICT",
        )


def downgrade() -> None:
    # History remains protected on downgrade as well.
    pass
