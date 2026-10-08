"""Pending refunds, one valid payment per reservation, cash-desk discrepancy.

- paiements.remboursement_demande_le: a paid reservation cancelled by
  someone who may not take money from a cash desk leaves a refund for a
  cashier to pay out.
- A reservation can have only one valid payment (prevents double payment
  when two requests arrive together).
- caisses.ecart_cloture: difference between the counted cash and the
  expected balance when the desk is closed.
"""

import sqlalchemy as sa
from alembic import op


revision = "0025_refunds_and_cash_close"
down_revision = "0024_gare_agents"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("paiements", sa.Column("remboursement_demande_le", sa.DateTime(timezone=True), nullable=True))
    op.create_index(
        "uq_paiement_valide_reservation", "paiements", ["id_reservation"], unique=True,
        postgresql_where=sa.text("statut = 'VALIDE'"),
    )
    op.add_column("caisses", sa.Column("ecart_cloture", sa.Numeric(12, 2), nullable=True))
    # Station agents run the cash desk, so they pay out pending refunds.
    op.execute(sa.text("""
        INSERT INTO roles_permissions (id_role, id_permission)
        SELECT r.id_role, p.id_permission FROM roles r, permissions p
        WHERE lower(r.libelle) = 'agent_gare' AND p.code = 'PAIEMENT_REFUND'
        ON CONFLICT DO NOTHING
    """))


def downgrade() -> None:
    op.execute(sa.text("""
        DELETE FROM roles_permissions rp USING roles r, permissions p
        WHERE rp.id_role = r.id_role AND rp.id_permission = p.id_permission
          AND lower(r.libelle) = 'agent_gare' AND p.code = 'PAIEMENT_REFUND'
    """))
    op.drop_column("caisses", "ecart_cloture")
    op.drop_index("uq_paiement_valide_reservation", table_name="paiements")
    op.drop_column("paiements", "remboursement_demande_le")
