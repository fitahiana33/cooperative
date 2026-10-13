"""Online payment idempotency fields and immutable audit log."""

import sqlalchemy as sa
from alembic import op


revision = "0030_online_payments_audit"
down_revision = "0029_seat_layout"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("paiements", sa.Column("fournisseur", sa.String(length=40), nullable=True))
    op.add_column("paiements", sa.Column("reference_fournisseur", sa.String(length=150), nullable=True))
    op.add_column("paiements", sa.Column("cle_idempotence", sa.String(length=100), nullable=True))
    op.add_column("paiements", sa.Column("webhook_recu_le", sa.DateTime(timezone=True), nullable=True))
    op.create_unique_constraint("uq_paiements_cle_idempotence", "paiements", ["cle_idempotence"])
    op.create_table(
        "audit_logs",
        sa.Column("id_audit_log", sa.BigInteger(), sa.Identity(always=True), primary_key=True),
        sa.Column("id_user", sa.BigInteger(), nullable=True),
        sa.Column("action", sa.String(length=80), nullable=False),
        sa.Column("entity_type", sa.String(length=80), nullable=False),
        sa.Column("entity_id", sa.String(length=80), nullable=True),
        sa.Column("before_data", sa.JSON(), nullable=True),
        sa.Column("after_data", sa.JSON(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["id_user"], ["users.id_user"], ondelete="SET NULL"),
    )
    op.create_index("idx_audit_logs_actor", "audit_logs", ["id_user"])
    op.create_index("idx_audit_logs_entity", "audit_logs", ["entity_type", "entity_id"])
    op.create_index("idx_audit_logs_created", "audit_logs", ["created_at"])


def downgrade() -> None:
    op.drop_index("idx_audit_logs_created", table_name="audit_logs")
    op.drop_index("idx_audit_logs_entity", table_name="audit_logs")
    op.drop_index("idx_audit_logs_actor", table_name="audit_logs")
    op.drop_table("audit_logs")
    op.drop_constraint("uq_paiements_cle_idempotence", "paiements", type_="unique")
    op.drop_column("paiements", "webhook_recu_le")
    op.drop_column("paiements", "cle_idempotence")
    op.drop_column("paiements", "reference_fournisseur")
    op.drop_column("paiements", "fournisseur")
