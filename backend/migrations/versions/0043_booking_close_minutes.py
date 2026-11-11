"""Make the reservation cut-off configurable per installation."""

from alembic import op
import sqlalchemy as sa


revision = "0043_booking_close_minutes"
down_revision = "0042_booking_settings"
branch_labels = None
depends_on = None


def upgrade():
    # A development database may already have received the column from an
    # interrupted local rollout. Keep this migration safe for both that case
    # and a clean deployment; Alembic only records the revision after success.
    op.execute(
        "ALTER TABLE booking_settings "
        "ADD COLUMN IF NOT EXISTS booking_close_minutes INTEGER NOT NULL DEFAULT 10"
    )
    op.execute(
        """
        DO $$ BEGIN
          IF NOT EXISTS (
            SELECT 1 FROM pg_constraint
            WHERE conname = 'ck_booking_settings_close_minutes'
          ) THEN
            ALTER TABLE booking_settings
            ADD CONSTRAINT ck_booking_settings_close_minutes
            CHECK (booking_close_minutes >= 0 AND booking_close_minutes <= 180);
          END IF;
        END $$;
        """
    )
    op.alter_column("booking_settings", "booking_close_minutes", server_default=None)


def downgrade():
    op.drop_constraint(
        "ck_booking_settings_close_minutes", "booking_settings", type_="check"
    )
    op.drop_column("booking_settings", "booking_close_minutes")
