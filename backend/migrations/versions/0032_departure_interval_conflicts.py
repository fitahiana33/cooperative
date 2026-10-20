"""Protect vehicle and driver planning intervals against concurrent inserts."""

import sqlalchemy as sa
from alembic import op


revision = "0032_departure_conflicts"
down_revision = "0031_cash_only"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(sa.text("CREATE EXTENSION IF NOT EXISTS btree_gist"))
    op.add_column("departs", sa.Column("planifie_depart_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("departs", sa.Column("planifie_arrivee_at", sa.DateTime(timezone=True), nullable=True))
    # Existing rows are backfilled with the route duration. Nulls are not
    # excluded by PostgreSQL exclusion constraints, so legacy data remains
    # deployable even when a route has no duration yet.
    op.execute(sa.text("""
        UPDATE departs AS d
        SET planifie_depart_at = (d.date_depart + d.heure_depart) AT TIME ZONE 'Indian/Antananarivo',
            planifie_arrivee_at = ((d.date_depart + d.heure_depart) AT TIME ZONE 'Indian/Antananarivo')
                + make_interval(mins => COALESCE(i.duree_estimee_minutes, 60))
        FROM itineraires AS i
        WHERE i.id_itineraire = d.id_itineraire
    """))
    op.execute(sa.text("""
        ALTER TABLE departs ADD CONSTRAINT ex_active_depart_vehicle_interval
        EXCLUDE USING gist (
            id_vehicule WITH =,
            tstzrange(planifie_depart_at, planifie_arrivee_at, '[)') WITH &&
        ) WHERE (statut NOT IN ('ANNULE', 'TERMINE') AND planifie_depart_at IS NOT NULL AND planifie_arrivee_at IS NOT NULL)
    """))
    op.execute(sa.text("""
        ALTER TABLE departs ADD CONSTRAINT ex_active_depart_driver_interval
        EXCLUDE USING gist (
            id_chauffeur WITH =,
            tstzrange(planifie_depart_at, planifie_arrivee_at, '[)') WITH &&
        ) WHERE (statut NOT IN ('ANNULE', 'TERMINE') AND planifie_depart_at IS NOT NULL AND planifie_arrivee_at IS NOT NULL)
    """))


def downgrade() -> None:
    op.execute(sa.text("ALTER TABLE departs DROP CONSTRAINT IF EXISTS ex_active_depart_driver_interval"))
    op.execute(sa.text("ALTER TABLE departs DROP CONSTRAINT IF EXISTS ex_active_depart_vehicle_interval"))
    op.drop_column("departs", "planifie_arrivee_at")
    op.drop_column("departs", "planifie_depart_at")
