"""Private, versioned user profile photos."""
import sqlalchemy as sa
from alembic import op

revision = "0041_user_photo"
down_revision = "0040_operational_reliability"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("photo_version", sa.String(32), nullable=True))


def downgrade():
    op.drop_column("users", "photo_version")
