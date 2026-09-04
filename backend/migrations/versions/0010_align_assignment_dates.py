"""Align assignment date validation with the PostgreSQL source schema."""

from alembic import op
import sqlalchemy as sa


revision = "0010_align_assignment_dates"
down_revision = "0009_assignment_integrity"
branch_labels = None
depends_on = None


def _has_check_constraint(inspector, table_name: str, constraint_name: str) -> bool:
    return any(
        constraint.get("name") == constraint_name
        for constraint in inspector.get_check_constraints(table_name)
    )


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table("vehicule_chauffeurs"):
        return

    if _has_check_constraint(inspector, "vehicule_chauffeurs", "ck_vehicule_chauffeur_dates"):
        op.drop_constraint(
            "ck_vehicule_chauffeur_dates",
            "vehicule_chauffeurs",
            type_="check",
        )

    op.create_check_constraint(
        "ck_vehicule_chauffeur_dates",
        "vehicule_chauffeurs",
        "date_fin IS NULL OR date_fin >= date_debut",
    )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table("vehicule_chauffeurs"):
        return

    if _has_check_constraint(inspector, "vehicule_chauffeurs", "ck_vehicule_chauffeur_dates"):
        op.drop_constraint(
            "ck_vehicule_chauffeur_dates",
            "vehicule_chauffeurs",
            type_="check",
        )

    # Historical same-day assignments must be closed before restoring the
    # stricter rule introduced by migration 0009.
    op.execute(
        sa.text(
            """
            UPDATE vehicule_chauffeurs
            SET date_fin = date_debut + 1
            WHERE date_fin IS NOT NULL AND date_fin = date_debut
            """
        )
    )
    op.create_check_constraint(
        "ck_vehicule_chauffeur_dates",
        "vehicule_chauffeurs",
        "date_fin IS NULL OR date_fin > date_debut",
    )
