"""Exclude blocked seats from reservation and occupancy counts."""

import sqlalchemy as sa
from alembic import op


revision = "0021_fix_occupancy_count"
down_revision = "0020_driver_pointage"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(sa.text("""
        CREATE OR REPLACE FUNCTION fn_sync_depart_places_count()
        RETURNS TRIGGER AS $$
        DECLARE v_depart BIGINT;
        BEGIN
            v_depart := COALESCE(NEW.id_depart, OLD.id_depart);
            UPDATE departs SET places_reservees = (
                SELECT COUNT(*) FROM depart_places
                WHERE id_depart = v_depart AND statut IN ('RESERVEE', 'OCCUPEE')
            ), updated_at = CURRENT_TIMESTAMP WHERE id_depart = v_depart;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        UPDATE departs d SET places_reservees = (
            SELECT COUNT(*) FROM depart_places p
            WHERE p.id_depart = d.id_depart AND p.statut IN ('RESERVEE', 'OCCUPEE')
        );
    """))


def downgrade() -> None:
    op.execute(sa.text("""
        CREATE OR REPLACE FUNCTION fn_sync_depart_places_count()
        RETURNS TRIGGER AS $$
        DECLARE v_depart BIGINT;
        BEGIN
            v_depart := COALESCE(NEW.id_depart, OLD.id_depart);
            UPDATE departs SET places_reservees = (
                SELECT COUNT(*) FROM depart_places
                WHERE id_depart = v_depart AND statut <> 'DISPONIBLE'
            ), updated_at = CURRENT_TIMESTAMP WHERE id_depart = v_depart;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """))
