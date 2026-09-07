"""Add departures and planning for Sprint 7."""

import sqlalchemy as sa
from alembic import op


revision = "0018_sprint7_departs"
down_revision = "0017_sprint6_routes_fares"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "departs",
        sa.Column("id_depart", sa.BigInteger(), sa.Identity(always=True), primary_key=True),
        sa.Column("id_itineraire", sa.BigInteger(), nullable=False),
        sa.Column("id_cooperative", sa.BigInteger(), nullable=False),
        sa.Column("id_vehicule", sa.BigInteger(), nullable=False),
        sa.Column("id_chauffeur", sa.BigInteger(), nullable=False),
        sa.Column("id_tarif", sa.BigInteger(), nullable=False),
        sa.Column("date_depart", sa.Date(), nullable=False),
        sa.Column("heure_depart", sa.Time(), nullable=False),
        sa.Column("nombre_places", sa.Integer(), nullable=False),
        sa.Column("places_reservees", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("statut", sa.String(20), nullable=False, server_default="PROGRAMME"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(
            ["id_itineraire"], ["itineraires.id_itineraire"],
            name="fk_departs_itineraire", ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["id_cooperative"], ["cooperatives.id_cooperative"],
            name="fk_departs_cooperative", ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["id_vehicule"], ["vehicules.id_vehicule"],
            name="fk_departs_vehicule", ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["id_chauffeur"], ["chauffeurs.id_chauffeur"],
            name="fk_departs_chauffeur", ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["id_tarif"], ["tarifs.id_tarif"],
            name="fk_departs_tarif", ondelete="RESTRICT",
        ),
        sa.CheckConstraint(
            "statut IN ('PROGRAMME', 'EMBARQUEMENT', 'RETARDE', 'PARTI', 'TERMINE', 'ANNULE')",
            name="ck_departs_statut",
        ),
        sa.CheckConstraint("nombre_places > 0", name="ck_departs_nombre_places"),
        sa.CheckConstraint(
            "places_reservees >= 0 AND places_reservees <= nombre_places",
            name="ck_departs_places_reservees",
        ),
    )

    for name, columns in (
        ("idx_departs_itineraire", ["id_itineraire"]),
        ("idx_departs_cooperative", ["id_cooperative"]),
        ("idx_departs_vehicule", ["id_vehicule"]),
        ("idx_departs_chauffeur", ["id_chauffeur"]),
        ("idx_departs_tarif", ["id_tarif"]),
        ("idx_departs_date_heure", ["date_depart", "heure_depart"]),
        ("idx_departs_statut", ["statut"]),
    ):
        op.create_index(name, "departs", columns)

    op.create_index(
        "uq_active_depart_vehicle_slot",
        "departs",
        ["id_vehicule", "date_depart", "heure_depart"],
        unique=True,
        postgresql_where=sa.text("statut <> 'ANNULE'"),
    )
    op.create_index(
        "uq_active_depart_driver_slot",
        "departs",
        ["id_chauffeur", "date_depart", "heure_depart"],
        unique=True,
        postgresql_where=sa.text("statut <> 'ANNULE'"),
    )


def downgrade() -> None:
    op.drop_index("uq_active_depart_driver_slot", table_name="departs")
    op.drop_index("uq_active_depart_vehicle_slot", table_name="departs")
    for name in (
        "idx_departs_statut",
        "idx_departs_date_heure",
        "idx_departs_tarif",
        "idx_departs_chauffeur",
        "idx_departs_vehicule",
        "idx_departs_cooperative",
        "idx_departs_itineraire",
    ):
        op.drop_index(name, table_name="departs")
    op.drop_table("departs")

