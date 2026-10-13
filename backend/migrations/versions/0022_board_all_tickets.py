"""Mark a reservation boarded only once all of its tickets are used.

The previous trigger moved the whole reservation to EMBARQUEE on the first
boarding, which made every other ticket of a multi-seat reservation fail the
"reservation must be paid" check.
"""

import sqlalchemy as sa
from alembic import op


revision = "0022_board_all_tickets"
down_revision = "0021_fix_occupancy_count"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(sa.text("""
        CREATE OR REPLACE FUNCTION fn_embarquement_valide()
        RETURNS TRIGGER AS $$
        DECLARE v_place BIGINT; v_reservation BIGINT;
        BEGIN
            IF NEW.statut = 'VALIDE' THEN
                SELECT rp.id_depart_place, rp.id_reservation INTO v_place, v_reservation
                FROM billets b JOIN reservation_places rp ON rp.id_reservation_place = b.id_reservation_place
                WHERE b.id_billet = NEW.id_billet;
                UPDATE billets SET statut = 'UTILISE', date_utilisation = NEW.date_heure_embarquement, updated_at = CURRENT_TIMESTAMP
                WHERE id_billet = NEW.id_billet;
                UPDATE depart_places SET statut = 'OCCUPEE', updated_at = CURRENT_TIMESTAMP
                WHERE id_depart_place = v_place;
                UPDATE reservations SET statut = 'EMBARQUEE', updated_at = CURRENT_TIMESTAMP
                WHERE id_reservation = v_reservation AND statut IN ('CONFIRMEE', 'PAYEE')
                  AND NOT EXISTS (
                      SELECT 1 FROM billets b
                      JOIN reservation_places rp ON rp.id_reservation_place = b.id_reservation_place
                      WHERE rp.id_reservation = v_reservation AND b.statut = 'VALIDE'
                  );
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """))


def downgrade() -> None:
    op.execute(sa.text("""
        CREATE OR REPLACE FUNCTION fn_embarquement_valide()
        RETURNS TRIGGER AS $$
        DECLARE v_place BIGINT; v_reservation BIGINT;
        BEGIN
            IF NEW.statut = 'VALIDE' THEN
                SELECT rp.id_depart_place, rp.id_reservation INTO v_place, v_reservation
                FROM billets b JOIN reservation_places rp ON rp.id_reservation_place = b.id_reservation_place
                WHERE b.id_billet = NEW.id_billet;
                UPDATE billets SET statut = 'UTILISE', date_utilisation = NEW.date_heure_embarquement, updated_at = CURRENT_TIMESTAMP
                WHERE id_billet = NEW.id_billet;
                UPDATE depart_places SET statut = 'OCCUPEE', updated_at = CURRENT_TIMESTAMP
                WHERE id_depart_place = v_place;
                UPDATE reservations SET statut = 'EMBARQUEE', updated_at = CURRENT_TIMESTAMP
                WHERE id_reservation = v_reservation AND statut IN ('CONFIRMEE', 'PAYEE');
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """))
