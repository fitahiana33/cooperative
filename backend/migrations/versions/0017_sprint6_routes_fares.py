"""Add Sprint 6 destinations, itineraries and fares."""

import sqlalchemy as sa
from alembic import op


revision = "0017_sprint6_routes_fares"
down_revision = "0016_cascade_vehicle_documents"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "destinations",
        sa.Column("id_destination", sa.BigInteger(), sa.Identity(always=True), primary_key=True),
        sa.Column("nom", sa.String(150), nullable=False),
        sa.Column("region", sa.String(100)),
        sa.Column("description", sa.Text()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("nom", name="uq_destinations_nom"),
    )

    op.create_table(
        "itineraires",
        sa.Column("id_itineraire", sa.BigInteger(), sa.Identity(always=True), primary_key=True),
        sa.Column("id_destination_depart", sa.BigInteger(), nullable=False),
        sa.Column("id_destination_arrivee", sa.BigInteger(), nullable=False),
        sa.Column("distance_km", sa.Numeric(8, 2)),
        sa.Column("duree_estimee_minutes", sa.Integer()),
        sa.Column("description", sa.Text()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(
            ["id_destination_depart"], ["destinations.id_destination"],
            name="fk_itineraires_destination_depart", ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["id_destination_arrivee"], ["destinations.id_destination"],
            name="fk_itineraires_destination_arrivee", ondelete="RESTRICT",
        ),
        sa.UniqueConstraint(
            "id_destination_depart", "id_destination_arrivee",
            name="uq_itineraire_depart_arrivee",
        ),
        sa.CheckConstraint(
            "id_destination_depart <> id_destination_arrivee",
            name="ck_itineraire_destinations_differentes",
        ),
        sa.CheckConstraint(
            "distance_km IS NULL OR distance_km > 0",
            name="ck_itineraire_distance_positive",
        ),
        sa.CheckConstraint(
            "duree_estimee_minutes IS NULL OR duree_estimee_minutes > 0",
            name="ck_itineraire_duree_positive",
        ),
    )

    op.create_table(
        "itineraire_cooperatives",
        sa.Column("id_itineraire", sa.BigInteger(), nullable=False),
        sa.Column("id_cooperative", sa.BigInteger(), nullable=False),
        sa.Column("date_debut", sa.Date(), nullable=False, server_default=sa.func.current_date()),
        sa.Column("date_fin", sa.Date()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(
            ["id_itineraire"], ["itineraires.id_itineraire"],
            name="fk_itineraire_cooperatives_itineraire", ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["id_cooperative"], ["cooperatives.id_cooperative"],
            name="fk_itineraire_cooperatives_cooperative", ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id_itineraire", "id_cooperative"),
        sa.CheckConstraint(
            "date_fin IS NULL OR date_fin >= date_debut",
            name="ck_itineraire_cooperative_dates",
        ),
    )

    op.create_table(
        "tarifs",
        sa.Column("id_tarif", sa.BigInteger(), sa.Identity(always=True), primary_key=True),
        sa.Column("id_itineraire", sa.BigInteger(), nullable=False),
        sa.Column("id_cooperative", sa.BigInteger()),
        sa.Column("prix", sa.Numeric(12, 2), nullable=False),
        sa.Column("devise", sa.String(10), nullable=False, server_default="MGA"),
        sa.Column("date_debut", sa.Date(), nullable=False, server_default=sa.func.current_date()),
        sa.Column("date_fin", sa.Date()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(
            ["id_itineraire"], ["itineraires.id_itineraire"],
            name="fk_tarifs_itineraire", ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["id_cooperative"], ["cooperatives.id_cooperative"],
            name="fk_tarifs_cooperative", ondelete="CASCADE",
        ),
        sa.CheckConstraint("prix > 0", name="ck_tarif_prix_positif"),
        sa.CheckConstraint(
            "date_fin IS NULL OR date_fin >= date_debut",
            name="ck_tarif_dates",
        ),
    )

    op.create_index("idx_destinations_nom", "destinations", ["nom"])
    op.create_index("idx_destinations_active", "destinations", ["is_active"])
    op.create_index("idx_itineraires_depart", "itineraires", ["id_destination_depart"])
    op.create_index("idx_itineraires_arrivee", "itineraires", ["id_destination_arrivee"])
    op.create_index("idx_itineraires_active", "itineraires", ["is_active"])
    op.create_index("idx_itineraire_cooperatives_itineraire", "itineraire_cooperatives", ["id_itineraire"])
    op.create_index("idx_itineraire_cooperatives_cooperative", "itineraire_cooperatives", ["id_cooperative"])
    op.create_index("idx_itineraire_cooperatives_active", "itineraire_cooperatives", ["is_active"])
    op.create_index(
        "uq_active_itineraire_cooperative",
        "itineraire_cooperatives",
        ["id_itineraire", "id_cooperative"],
        unique=True,
        postgresql_where=sa.text("is_active = TRUE"),
    )
    op.create_index("idx_tarifs_itineraire", "tarifs", ["id_itineraire"])
    op.create_index("idx_tarifs_cooperative", "tarifs", ["id_cooperative"])
    op.create_index("idx_tarifs_active", "tarifs", ["is_active"])
    op.create_index("idx_tarifs_dates", "tarifs", ["date_debut", "date_fin"])
    op.create_index(
        "uq_active_tarif_general", "tarifs", ["id_itineraire"], unique=True,
        postgresql_where=sa.text("is_active = TRUE AND id_cooperative IS NULL"),
    )
    op.create_index(
        "uq_active_tarif_cooperative", "tarifs", ["id_itineraire", "id_cooperative"], unique=True,
        postgresql_where=sa.text("is_active = TRUE AND id_cooperative IS NOT NULL"),
    )


def downgrade() -> None:
    for name, table in (
        ("uq_active_tarif_cooperative", "tarifs"),
        ("uq_active_tarif_general", "tarifs"),
        ("idx_tarifs_dates", "tarifs"),
        ("idx_tarifs_active", "tarifs"),
        ("idx_tarifs_cooperative", "tarifs"),
        ("idx_tarifs_itineraire", "tarifs"),
        ("uq_active_itineraire_cooperative", "itineraire_cooperatives"),
        ("idx_itineraire_cooperatives_active", "itineraire_cooperatives"),
        ("idx_itineraire_cooperatives_cooperative", "itineraire_cooperatives"),
        ("idx_itineraire_cooperatives_itineraire", "itineraire_cooperatives"),
        ("idx_itineraires_active", "itineraires"),
        ("idx_itineraires_arrivee", "itineraires"),
        ("idx_itineraires_depart", "itineraires"),
        ("idx_destinations_active", "destinations"),
        ("idx_destinations_nom", "destinations"),
    ):
        op.drop_index(name, table_name=table)
    op.drop_table("tarifs")
    op.drop_table("itineraire_cooperatives")
    op.drop_table("itineraires")
    op.drop_table("destinations")
