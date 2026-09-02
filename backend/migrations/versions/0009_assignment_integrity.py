"""Enforce one active vehicle assignment per driver and valid assignment dates."""

from alembic import op
import sqlalchemy as sa


revision = "0009_assignment_integrity"
down_revision = "0008_revoked_tokens"
branch_labels = None
depends_on = None


def _has_check_constraint(inspector, table_name: str, constraint_name: str) -> bool:
    return any(
        constraint.get("name") == constraint_name
        for constraint in inspector.get_check_constraints(table_name)
    )


def _has_index(inspector, table_name: str, index_name: str) -> bool:
    return any(index.get("name") == index_name for index in inspector.get_indexes(table_name))


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table("vehicule_chauffeurs"):
        return

    # Keep the most recent active assignment when old data contains duplicates.
    op.execute(
        sa.text(
            """
            WITH ranked AS (
                SELECT
                    id_vehicule,
                    id_chauffeur,
                    date_debut,
                    ROW_NUMBER() OVER (
                        PARTITION BY id_chauffeur
                        ORDER BY date_debut DESC, created_at DESC, id_vehicule DESC
                    ) AS row_number
                FROM vehicule_chauffeurs
                WHERE is_active = TRUE
            )
            UPDATE vehicule_chauffeurs AS assignment
            SET is_active = FALSE
            FROM ranked
            WHERE assignment.id_vehicule = ranked.id_vehicule
              AND assignment.id_chauffeur = ranked.id_chauffeur
              AND assignment.date_debut = ranked.date_debut
              AND ranked.row_number > 1
            """
        )
    )

    if not _has_index(inspector, "vehicule_chauffeurs", "uq_active_chauffeur_assignment"):
        op.create_index(
            "uq_active_chauffeur_assignment",
            "vehicule_chauffeurs",
            ["id_chauffeur"],
            unique=True,
            postgresql_where=sa.text("is_active = TRUE"),
        )

    inspector = sa.inspect(bind)
    if _has_check_constraint(inspector, "vehicule_chauffeurs", "ck_vehicule_chauffeur_dates"):
        op.drop_constraint(
            "ck_vehicule_chauffeur_dates",
            "vehicule_chauffeurs",
            type_="check",
        )

    # NOT VALID lets PostgreSQL install the rule without blocking an existing
    # database containing historical zero-day assignments.
    op.execute(
        sa.text(
            """
            ALTER TABLE vehicule_chauffeurs
            ADD CONSTRAINT ck_vehicule_chauffeur_dates
            CHECK (date_fin IS NULL OR date_fin > date_debut)
            NOT VALID
            """
        )
    )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table("vehicule_chauffeurs"):
        return

    if _has_index(inspector, "vehicule_chauffeurs", "uq_active_chauffeur_assignment"):
        op.drop_index("uq_active_chauffeur_assignment", table_name="vehicule_chauffeurs")

    inspector = sa.inspect(bind)
    if _has_check_constraint(inspector, "vehicule_chauffeurs", "ck_vehicule_chauffeur_dates"):
        op.drop_constraint(
            "ck_vehicule_chauffeur_dates",
            "vehicule_chauffeurs",
            type_="check",
        )

    op.execute(
        sa.text(
            """
            ALTER TABLE vehicule_chauffeurs
            ADD CONSTRAINT ck_vehicule_chauffeur_dates
            CHECK (date_fin IS NULL OR date_fin >= date_debut)
            """
        )
    )
