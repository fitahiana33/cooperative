"""Editable deposit percentage and stable conditions for existing bookings."""

from alembic import op
import sqlalchemy as sa

revision = "0042_booking_settings"
down_revision = "0041_user_photo"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "booking_settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("deposit_percentage", sa.Numeric(5, 2), nullable=False),
        sa.Column(
            "updated_by",
            sa.BigInteger(),
            sa.ForeignKey("users.id_user", ondelete="SET NULL"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint("id = 1", name="ck_booking_settings_singleton"),
        sa.CheckConstraint(
            "deposit_percentage > 0 AND deposit_percentage <= 100",
            name="ck_booking_settings_percentage",
        ),
    )
    op.add_column("reservations", sa.Column("taux_acompte", sa.Numeric(5, 4)))
    op.add_column("reservations", sa.Column("plancher_acompte", sa.Numeric(12, 2)))
    op.create_check_constraint(
        "ck_reservations_taux_acompte",
        "reservations",
        "taux_acompte IS NULL OR (taux_acompte > 0 AND taux_acompte <= 1)",
    )
    op.create_check_constraint(
        "ck_reservations_plancher_acompte",
        "reservations",
        "plancher_acompte IS NULL OR plancher_acompte >= 0",
    )


def downgrade():
    op.drop_constraint(
        "ck_reservations_plancher_acompte", "reservations", type_="check"
    )
    op.drop_constraint("ck_reservations_taux_acompte", "reservations", type_="check")
    op.drop_column("reservations", "plancher_acompte")
    op.drop_column("reservations", "taux_acompte")
    op.drop_table("booking_settings")
