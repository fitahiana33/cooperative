"""Add vehicle, vehicle-document and driver management (Sprint 5)."""

from alembic import op
import sqlalchemy as sa


revision = "0007_fleet"
down_revision = "0006_coop_created_at"
branch_labels = None
depends_on = None


def _create_if_missing(name: str, *columns, **kwargs) -> None:
    if not sa.inspect(op.get_bind()).has_table(name):
        op.create_table(name, *columns, **kwargs)


def upgrade() -> None:
    _create_if_missing(
        "marques",
        sa.Column("id_marque", sa.BigInteger(), sa.Identity(always=True), primary_key=True),
        sa.Column("nom", sa.String(100), nullable=False, unique=True),
        sa.Column("description", sa.Text()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    _create_if_missing(
        "modeles",
        sa.Column("id_modele", sa.BigInteger(), sa.Identity(always=True), primary_key=True),
        sa.Column("id_marque", sa.BigInteger(), sa.ForeignKey("marques.id_marque", ondelete="RESTRICT"), nullable=False),
        sa.Column("nom", sa.String(100), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("id_marque", "nom", name="uq_modele_marque_nom"),
    )
    _create_if_missing(
        "vehicules",
        sa.Column("id_vehicule", sa.BigInteger(), sa.Identity(always=True), primary_key=True),
        sa.Column("id_modele", sa.BigInteger(), sa.ForeignKey("modeles.id_modele", ondelete="RESTRICT"), nullable=False),
        sa.Column("id_cooperative", sa.BigInteger(), sa.ForeignKey("cooperatives.id_cooperative", ondelete="RESTRICT"), nullable=False),
        sa.Column("immatriculation", sa.String(30), nullable=False, unique=True),
        sa.Column("chevaux", sa.Integer()),
        sa.Column("nombre_places", sa.Integer(), nullable=False),
        sa.Column("disponibilite", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("etat", sa.String(50), nullable=False, server_default="BON_ETAT"),
        sa.Column("description", sa.Text()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("chevaux IS NULL OR chevaux > 0", name="ck_vehicule_chevaux"),
        sa.CheckConstraint("nombre_places > 0", name="ck_vehicule_nombre_places"),
        sa.CheckConstraint("etat IN ('BON_ETAT', 'MOYEN', 'A_REPARER', 'HORS_SERVICE')", name="ck_vehicule_etat"),
    )
    _create_if_missing(
        "vehicule_documents",
        sa.Column("id_document", sa.BigInteger(), sa.Identity(always=True), primary_key=True),
        sa.Column("id_vehicule", sa.BigInteger(), sa.ForeignKey("vehicules.id_vehicule", ondelete="CASCADE"), nullable=False),
        sa.Column("type_document", sa.String(50), nullable=False),
        sa.Column("numero_document", sa.String(100)),
        sa.Column("date_delivrance", sa.Date()),
        sa.Column("date_expiration", sa.Date()),
        sa.Column("fichier_path", sa.String(500)),
        sa.Column("is_valid", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("type_document IN ('CARTE_GRISE', 'ASSURANCE', 'VISITE_TECHNIQUE')", name="ck_vehicule_document_type"),
        sa.CheckConstraint("date_expiration IS NULL OR date_delivrance IS NULL OR date_expiration >= date_delivrance", name="ck_vehicule_document_dates"),
    )
    _create_if_missing(
        "chauffeurs",
        sa.Column("id_chauffeur", sa.BigInteger(), sa.Identity(always=True), primary_key=True),
        sa.Column("id_user", sa.BigInteger(), sa.ForeignKey("users.id_user", ondelete="RESTRICT"), nullable=False, unique=True),
        sa.Column("id_cooperative", sa.BigInteger(), sa.ForeignKey("cooperatives.id_cooperative", ondelete="RESTRICT"), nullable=False),
        sa.Column("numero_permis", sa.String(100), nullable=False, unique=True),
        sa.Column("categorie_permis", sa.String(20), nullable=False),
        sa.Column("date_expiration_permis", sa.Date(), nullable=False),
        sa.Column("disponibilite", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    _create_if_missing(
        "vehicule_chauffeurs",
        sa.Column("id_vehicule", sa.BigInteger(), sa.ForeignKey("vehicules.id_vehicule", ondelete="CASCADE"), primary_key=True),
        sa.Column("id_chauffeur", sa.BigInteger(), sa.ForeignKey("chauffeurs.id_chauffeur", ondelete="CASCADE"), primary_key=True),
        sa.Column("date_debut", sa.Date(), primary_key=True, server_default=sa.func.current_date()),
        sa.Column("date_fin", sa.Date()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("date_fin IS NULL OR date_fin >= date_debut", name="ck_vehicule_chauffeur_dates"),
    )


def downgrade() -> None:
    bind = op.get_bind()
    for table in ("vehicule_chauffeurs", "chauffeurs", "vehicule_documents", "vehicules", "modeles", "marques"):
        if sa.inspect(bind).has_table(table):
            op.drop_table(table)
