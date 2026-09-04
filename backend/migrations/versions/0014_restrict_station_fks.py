"""Protect station resources from accidental hard-delete cascades."""

from alembic import op


revision = "0014_restrict_station_fks"
down_revision = "0013_finalize_constraints"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # A previous interrupted migration may have applied the CASCADE DDL before
    # failing while updating alembic_version. Restore the safe policy used by
    # the application: station resources are deactivated explicitly and are
    # never removed implicitly with their station.
    foreign_keys = (
        ("quais", "fk_quais_gare", "gares", ["id_gare"], ["id_gare"]),
        ("zones", "fk_zones_gare", "gares", ["id_gare"], ["id_gare"]),
        ("emplacements", "fk_emplacements_zone", "zones", ["id_zone"], ["id_zone"]),
    )
    for table, constraint_name, referred_table, local_columns, remote_columns in foreign_keys:
        op.drop_constraint(constraint_name, table, type_="foreignkey")
        op.create_foreign_key(
            constraint_name,
            table,
            referred_table,
            local_columns,
            remote_columns,
            ondelete="RESTRICT",
        )


def downgrade() -> None:
    # Keep the safe RESTRICT policy on downgrade as well.
    pass
