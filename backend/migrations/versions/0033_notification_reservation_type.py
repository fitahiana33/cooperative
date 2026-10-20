"""Allow reservation modification notifications."""

import sqlalchemy as sa
from alembic import op


revision = "0033_notification_type"
down_revision = "0032_departure_conflicts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint("ck_notification_type", "notifications", type_="check")
    op.create_check_constraint(
        "ck_notification_type",
        "notifications",
        "type_notification IN ('CONFIRMATION_RESERVATION', 'CONFIRMATION_PAIEMENT', 'RAPPEL_DEPART', 'RETARD', 'ANNULATION', 'MODIFICATION_HORAIRE', 'CONFIRMATION_EMBARQUEMENT', 'EXPIRATION_DOCUMENT', 'MODIFICATION_RESERVATION')",
    )


def downgrade() -> None:
    op.execute(sa.text("DELETE FROM notifications WHERE type_notification = 'MODIFICATION_RESERVATION'"))
    op.drop_constraint("ck_notification_type", "notifications", type_="check")
    op.create_check_constraint(
        "ck_notification_type",
        "notifications",
        "type_notification IN ('CONFIRMATION_RESERVATION', 'CONFIRMATION_PAIEMENT', 'RAPPEL_DEPART', 'RETARD', 'ANNULATION', 'MODIFICATION_HORAIRE', 'CONFIRMATION_EMBARQUEMENT', 'EXPIRATION_DOCUMENT')",
    )
