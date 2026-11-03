"""Associate each departure with its station of origin."""

import sqlalchemy as sa
from alembic import op


revision = "0035_departure_station"
down_revision = "0034_passenger_res_update"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("departs", sa.Column("id_gare", sa.BigInteger(), nullable=True))
    op.create_foreign_key(
        "fk_departs_gare",
        "departs",
        "gares",
        ["id_gare"],
        ["id_gare"],
        ondelete="RESTRICT",
    )
    op.create_index("idx_departs_gare", "departs", ["id_gare"])

    # Backfill unambiguous historical rows from the route's origin city and
    # the cooperative's active station associations. Ambiguous rows remain
    # nullable and must be assigned before being edited again.
    op.execute(sa.text("""
        UPDATE departs AS d
        SET id_gare = candidates.id_gare
        FROM (
            SELECT d0.id_depart, MIN(g.id_gare) AS id_gare
            FROM departs d0
            JOIN itineraires i ON i.id_itineraire = d0.id_itineraire
            JOIN destinations origin ON origin.id_destination = i.id_destination_depart
            JOIN gare_cooperatives gc ON gc.id_cooperative = d0.id_cooperative
                AND gc.is_active = TRUE
            JOIN gares g ON g.id_gare = gc.id_gare
                AND g.is_active = TRUE
                AND lower(g.ville) = lower(origin.nom)
            WHERE d0.id_gare IS NULL
            GROUP BY d0.id_depart
            HAVING COUNT(*) = 1
        ) AS candidates
        WHERE d.id_depart = candidates.id_depart
    """))


def downgrade() -> None:
    op.drop_index("idx_departs_gare", table_name="departs")
    op.drop_constraint("fk_departs_gare", "departs", type_="foreignkey")
    op.drop_column("departs", "id_gare")
