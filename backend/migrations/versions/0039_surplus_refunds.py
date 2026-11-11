"""Refunding a surplus receipt must preserve the fully funded reservation."""

from alembic import op

revision = "0039_surplus_refunds"
down_revision = "0038_assignment_cancellation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE OR REPLACE FUNCTION fn_paiement_maj_reservation()
        RETURNS TRIGGER AS $$
        BEGIN
            IF NEW.statut = 'VALIDE' THEN
                UPDATE reservations SET statut = 'PAYEE', updated_at = CURRENT_TIMESTAMP
                WHERE id_reservation = NEW.id_reservation AND statut IN ('EN_ATTENTE', 'CONFIRMEE');
            ELSIF NEW.statut = 'REMBOURSE' THEN
                UPDATE reservations r SET statut = 'ANNULEE', updated_at = CURRENT_TIMESTAMP
                WHERE r.id_reservation = NEW.id_reservation
                  AND r.statut NOT IN ('ANNULEE', 'EXPIREE', 'TERMINEE')
                  AND NOT (NEW.remboursement_demande_le IS NOT NULL AND (
                    SELECT COALESCE(SUM(p.montant), 0) FROM paiements p
                    WHERE p.id_reservation = NEW.id_reservation AND p.id_paiement <> NEW.id_paiement
                      AND p.statut = 'VALIDE' AND p.remboursement_demande_le IS NULL
                  ) >= r.montant_total);
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)


def downgrade() -> None:
    op.execute("""
        CREATE OR REPLACE FUNCTION fn_paiement_maj_reservation()
        RETURNS TRIGGER AS $$
        BEGIN
            IF NEW.statut = 'VALIDE' THEN
                UPDATE reservations SET statut = 'PAYEE', updated_at = CURRENT_TIMESTAMP
                WHERE id_reservation = NEW.id_reservation AND statut IN ('EN_ATTENTE', 'CONFIRMEE');
            ELSIF NEW.statut = 'REMBOURSE' THEN
                UPDATE reservations SET statut = 'ANNULEE', updated_at = CURRENT_TIMESTAMP
                WHERE id_reservation = NEW.id_reservation AND statut NOT IN ('ANNULEE', 'EXPIREE', 'TERMINEE');
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
