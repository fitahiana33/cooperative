"""Prevent one vehicle from having multiple active drivers."""

from alembic import op
import sqlalchemy as sa


# Alembic's default version_num column is VARCHAR(32).
revision = "0011_unique_vehicle_assignment"
down_revision = "0010_align_assignment_dates"
branch_labels = None
depends_on = None


def _has_index(inspector, table_name: str, index_name: str) -> bool:
    return any(index.get("name") == index_name for index in inspector.get_indexes(table_name))


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table("vehicule_chauffeurs"):
        return

    # Keep the most recent active assignment for each vehicle before adding
    # the PostgreSQL partial unique index.
    op.execute(
        sa.text(
            """
            WITH ranked AS (
                SELECT
                    id_vehicule,
                    id_chauffeur,
                    date_debut,
                    ROW_NUMBER() OVER (
                        PARTITION BY id_vehicule
                        ORDER BY date_debut DESC, created_at DESC, id_chauffeur DESC
                    ) AS row_number
                FROM vehicule_chauffeurs
                WHERE is_active = TRUE
            )
            UPDATE vehicule_chauffeurs AS assignment
            SET is_active = FALSE,
                date_fin = GREATEST(CURRENT_DATE, assignment.date_debut)
            FROM ranked
            WHERE assignment.id_vehicule = ranked.id_vehicule
              AND assignment.id_chauffeur = ranked.id_chauffeur
              AND assignment.date_debut = ranked.date_debut
              AND ranked.row_number > 1
            """
        )
    )

    if not _has_index(inspector, "vehicule_chauffeurs", "uq_active_vehicle_assignment"):
        op.create_index(
            "uq_active_vehicle_assignment",
            "vehicule_chauffeurs",
            ["id_vehicule"],
            unique=True,
            postgresql_where=sa.text("is_active = TRUE"),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if inspector.has_table("vehicule_chauffeurs") and _has_index(
        inspector,
        "vehicule_chauffeurs",
        "uq_active_vehicle_assignment",
    ):
        op.drop_index("uq_active_vehicle_assignment", table_name="vehicule_chauffeurs")
