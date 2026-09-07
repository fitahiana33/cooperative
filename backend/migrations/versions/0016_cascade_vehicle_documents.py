"""Delete vehicle documents together with their vehicle."""

from alembic import op


revision = "0016_cascade_vehicle_documents"
down_revision = "0015_restrict_fleet_history"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint(
        "fk_vehicule_document_vehicule",
        "vehicule_documents",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "fk_vehicule_document_vehicule",
        "vehicule_documents",
        "vehicules",
        ["id_vehicule"],
        ["id_vehicule"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_vehicule_document_vehicule",
        "vehicule_documents",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "fk_vehicule_document_vehicule",
        "vehicule_documents",
        "vehicules",
        ["id_vehicule"],
        ["id_vehicule"],
        ondelete="RESTRICT",
    )
