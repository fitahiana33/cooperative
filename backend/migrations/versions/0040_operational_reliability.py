"""Booking recovery, financial event dates, scoped audit and notification delivery."""
import sqlalchemy as sa
from alembic import op

revision = "0040_operational_reliability"
down_revision = "0039_surplus_refunds"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint("ck_notification_canal", "notifications", type_="check")
    op.create_check_constraint("ck_notification_canal", "notifications", "canal IN ('IN_APP', 'PUSH', 'SMS', 'EMAIL')")
    op.execute("UPDATE notifications SET canal = 'IN_APP' WHERE canal = 'PUSH'")
    op.alter_column("notifications", "canal", server_default="IN_APP")
    op.add_column("reservations", sa.Column("commande_hash", sa.String(64)))
    op.create_unique_constraint("uq_reservations_commande_hash", "reservations", ["commande_hash"])
    op.add_column("reservations", sa.Column("commande_payload_hash", sa.String(64)))
    op.add_column("paiements", sa.Column("date_validation", sa.DateTime(timezone=True)))
    op.add_column("paiements", sa.Column("date_remboursement", sa.DateTime(timezone=True)))
    op.add_column("paiements", sa.Column("verification_requise", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("paiements", sa.Column("methode_remboursement", sa.String(30)))
    op.add_column("paiements", sa.Column("reference_remboursement", sa.String(150)))
    op.execute("UPDATE paiements SET date_validation = COALESCE(webhook_recu_le, date_paiement) WHERE statut IN ('VALIDE', 'REMBOURSE')")
    op.execute("UPDATE paiements SET verification_requise = true WHERE fournisseur = 'papi' AND statut = 'EN_ATTENTE' AND checkout_url IS NULL")
    op.add_column("operations_caisse", sa.Column("id_agent", sa.BigInteger(), sa.ForeignKey("users.id_user", ondelete="SET NULL")))
    for field, target in [("id_gare", "gares.id_gare"), ("id_cooperative", "cooperatives.id_cooperative")]:
        op.add_column("audit_logs", sa.Column(field, sa.BigInteger(), sa.ForeignKey(target, ondelete="SET NULL")))
        op.create_index("idx_audit_logs_" + field, "audit_logs", [field])
    op.execute("UPDATE audit_logs a SET id_gare=d.id_gare, id_cooperative=d.id_cooperative FROM departs d WHERE a.entity_type='depart' AND a.entity_id=d.id_depart::text")
    op.execute("UPDATE audit_logs a SET id_gare=d.id_gare, id_cooperative=d.id_cooperative FROM reservations r JOIN departs d ON d.id_depart=r.id_depart WHERE a.entity_type='reservation' AND a.entity_id=r.id_reservation::text")
    op.execute("UPDATE audit_logs a SET id_gare=d.id_gare, id_cooperative=d.id_cooperative FROM paiements p JOIN reservations r ON r.id_reservation=p.id_reservation JOIN departs d ON d.id_depart=r.id_depart WHERE a.entity_type='paiement' AND a.entity_id=p.id_paiement::text")
    op.execute("UPDATE audit_logs a SET id_gare=c.id_gare FROM caisses c WHERE a.entity_type='caisse' AND a.entity_id=c.id_caisse::text")
    # Existing audit entries with no scope remain visible to administrators only.
    for name, column in [
        ("delivery_status", sa.Column("delivery_status", sa.String(20), nullable=False, server_default="IN_APP")),
        ("delivery_attempts", sa.Column("delivery_attempts", sa.Integer(), nullable=False, server_default="0")),
        ("next_attempt_at", sa.Column("next_attempt_at", sa.DateTime(timezone=True))),
        ("delivered_at", sa.Column("delivered_at", sa.DateTime(timezone=True))),
        ("delivery_error", sa.Column("delivery_error", sa.String(255))),
    ]:
        op.add_column("notifications", column)
    op.create_index("idx_notifications_delivery", "notifications", ["delivery_status", "next_attempt_at"])


def downgrade():
    op.alter_column("notifications", "canal", server_default="PUSH")
    op.execute("UPDATE notifications SET canal = 'PUSH' WHERE canal = 'IN_APP'")
    op.drop_constraint("ck_notification_canal", "notifications", type_="check")
    op.create_check_constraint("ck_notification_canal", "notifications", "canal IN ('PUSH', 'SMS', 'EMAIL')")
    op.drop_index("idx_notifications_delivery", table_name="notifications")
    for name in ["delivery_status", "delivery_attempts", "next_attempt_at", "delivered_at", "delivery_error"]:
        op.drop_column("notifications", name)
    for name in ["id_gare", "id_cooperative"]:
        op.drop_index("idx_audit_logs_" + name, table_name="audit_logs")
        op.drop_column("audit_logs", name)
    op.drop_column("operations_caisse", "id_agent")
    for name in ["date_validation", "date_remboursement", "verification_requise", "methode_remboursement", "reference_remboursement"]:
        op.drop_column("paiements", name)
    op.drop_column("reservations", "commande_payload_hash")
    op.drop_column("reservations", "commande_hash")
