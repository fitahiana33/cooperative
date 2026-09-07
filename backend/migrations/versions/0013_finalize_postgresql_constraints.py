"""Finalize safe PostgreSQL constraints without widening delete cascades."""

from alembic import op
import sqlalchemy as sa


# Keep revision identifiers below PostgreSQL's default varchar(32) limit.
revision = "0013_finalize_constraints"
down_revision = "0012_align_postgresql_contract"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()

    # Keep station resources protected by RESTRICT. The application already
    # provides explicit deactivation, so a hard delete cannot erase related
    # quais, zones or emplacements by accident.
    has_email_constraint = bind.execute(sa.text(
        """
        SELECT 1
        FROM pg_constraint c
        JOIN pg_class t ON t.oid = c.conrelid
        WHERE c.conname = 'uq_users_email'
          AND t.relname = 'users'
          AND c.contype = 'u'
        """
    )).first()
    if not has_email_constraint:
        op.create_unique_constraint("uq_users_email", "users", ["email"])

    # Remove the obsolete SQLAlchemy-generated index name. The canonical
    # idx_users_email index was already created by migration 0012.
    bind.execute(sa.text(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM pg_class WHERE relname = 'ix_users_email' AND relkind = 'i'
            ) AND NOT EXISTS (
                SELECT 1 FROM pg_constraint WHERE conname = 'ix_users_email'
            ) THEN
                DROP INDEX ix_users_email;
            END IF;
        END $$;
        """
    ))


def downgrade() -> None:
    # The safe cleanup is intentionally not reverted to the obsolete index.
    pass
