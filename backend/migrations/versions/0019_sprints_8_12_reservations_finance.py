"""Add reservations, tickets, boarding, finance and notifications."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision = "0019_s8_s12_finance"
down_revision = "0018_sprint7_departs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    op.create_table(
        "depart_places",
        sa.Column("id_depart_place", sa.BigInteger(), sa.Identity(always=True), primary_key=True),
        sa.Column("id_depart", sa.BigInteger(), nullable=False),
        sa.Column("numero_place", sa.Integer(), nullable=False),
        sa.Column("statut", sa.String(20), nullable=False, server_default="DISPONIBLE"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["id_depart"], ["departs.id_depart"], name="fk_depart_place_depart", ondelete="CASCADE"),
        sa.UniqueConstraint("id_depart", "numero_place", name="uq_depart_place_numero"),
        sa.CheckConstraint("numero_place > 0", name="ck_depart_place_numero"),
        sa.CheckConstraint("statut IN ('DISPONIBLE', 'RESERVEE', 'BLOQUEE', 'OCCUPEE')", name="ck_depart_place_statut"),
    )

    op.create_table(
        "reservations",
        sa.Column("id_reservation", sa.BigInteger(), sa.Identity(always=True), primary_key=True),
        sa.Column("numero_reservation", sa.String(30), nullable=False),
        sa.Column("id_depart", sa.BigInteger(), nullable=False),
        sa.Column("id_user", sa.BigInteger(), nullable=False),
        sa.Column("montant_total", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("statut", sa.String(20), nullable=False, server_default="EN_ATTENTE"),
        sa.Column("date_expiration", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["id_depart"], ["departs.id_depart"], name="fk_reservation_depart", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["id_user"], ["users.id_user"], name="fk_reservation_user", ondelete="RESTRICT"),
        sa.UniqueConstraint("numero_reservation", name="uq_reservation_numero"),
        sa.CheckConstraint("statut IN ('EN_ATTENTE', 'CONFIRMEE', 'PAYEE', 'ANNULEE', 'EXPIREE', 'EMBARQUEE', 'TERMINEE')", name="ck_reservation_statut"),
        sa.CheckConstraint("montant_total >= 0", name="ck_reservation_montant"),
    )

    op.create_table(
        "reservation_places",
        sa.Column("id_reservation_place", sa.BigInteger(), sa.Identity(always=True), primary_key=True),
        sa.Column("id_reservation", sa.BigInteger(), nullable=False),
        sa.Column("id_depart_place", sa.BigInteger(), nullable=False),
        sa.Column("nom_passager", sa.String(150), nullable=False),
        sa.Column("telephone_passager", sa.String(30)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["id_reservation"], ["reservations.id_reservation"], name="fk_reservation_place_reservation", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["id_depart_place"], ["depart_places.id_depart_place"], name="fk_reservation_place_place", ondelete="RESTRICT"),
        sa.UniqueConstraint("id_reservation", "id_depart_place", name="uq_reservation_place"),
    )

    op.create_table(
        "billets",
        sa.Column("id_billet", sa.BigInteger(), sa.Identity(always=True), primary_key=True),
        sa.Column("numero_billet", sa.String(50), nullable=False),
        sa.Column("id_reservation_place", sa.BigInteger(), nullable=False),
        sa.Column("qr_code_uuid", postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("qr_code_path", sa.String(500)),
        sa.Column("statut", sa.String(20), nullable=False, server_default="VALIDE"),
        sa.Column("date_emission", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("date_utilisation", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["id_reservation_place"], ["reservation_places.id_reservation_place"], name="fk_billet_reservation_place", ondelete="RESTRICT"),
        sa.UniqueConstraint("numero_billet", name="uq_billet_numero"),
        sa.UniqueConstraint("qr_code_uuid", name="uq_billet_qr_code"),
        sa.UniqueConstraint("id_reservation_place", name="uq_billet_reservation_place"),
        sa.CheckConstraint("statut IN ('VALIDE', 'UTILISE', 'ANNULE', 'EXPIRE')", name="ck_billet_statut"),
    )

    op.create_table(
        "embarquements",
        sa.Column("id_embarquement", sa.BigInteger(), sa.Identity(always=True), primary_key=True),
        sa.Column("id_billet", sa.BigInteger(), nullable=False),
        sa.Column("id_agent", sa.BigInteger(), nullable=False),
        sa.Column("date_heure_embarquement", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("statut", sa.String(20), nullable=False, server_default="VALIDE"),
        sa.Column("motif_refus", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["id_billet"], ["billets.id_billet"], name="fk_embarquement_billet", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["id_agent"], ["users.id_user"], name="fk_embarquement_agent", ondelete="RESTRICT"),
        sa.CheckConstraint("statut IN ('VALIDE', 'REFUSE')", name="ck_embarquement_statut"),
        sa.CheckConstraint("(statut = 'REFUSE' AND motif_refus IS NOT NULL) OR statut = 'VALIDE'", name="ck_embarquement_motif_refus"),
    )

    op.create_table(
        "paiements",
        sa.Column("id_paiement", sa.BigInteger(), sa.Identity(always=True), primary_key=True),
        sa.Column("id_reservation", sa.BigInteger(), nullable=False),
        sa.Column("montant", sa.Numeric(12, 2), nullable=False),
        sa.Column("methode", sa.String(30), nullable=False, server_default="ESPECES"),
        sa.Column("reference_paiement", sa.String(100)),
        sa.Column("statut", sa.String(20), nullable=False, server_default="EN_ATTENTE"),
        sa.Column("date_paiement", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("id_agent", sa.BigInteger()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["id_reservation"], ["reservations.id_reservation"], name="fk_paiement_reservation", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["id_agent"], ["users.id_user"], name="fk_paiement_agent", ondelete="SET NULL"),
        sa.CheckConstraint("montant > 0", name="ck_paiement_montant"),
        sa.CheckConstraint("methode IN ('ESPECES', 'MOBILE_MONEY', 'CARTE', 'VIREMENT', 'AUTRE')", name="ck_paiement_methode"),
        sa.CheckConstraint("statut IN ('EN_ATTENTE', 'VALIDE', 'ECHOUE', 'REMBOURSE')", name="ck_paiement_statut"),
    )

    op.create_table(
        "caisses",
        sa.Column("id_caisse", sa.BigInteger(), sa.Identity(always=True), primary_key=True),
        sa.Column("id_gare", sa.BigInteger(), nullable=False),
        sa.Column("id_agent", sa.BigInteger(), nullable=False),
        sa.Column("date_ouverture", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("montant_ouverture", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("date_cloture", sa.DateTime(timezone=True)),
        sa.Column("montant_cloture", sa.Numeric(12, 2)),
        sa.Column("statut", sa.String(20), nullable=False, server_default="OUVERTE"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["id_gare"], ["gares.id_gare"], name="fk_caisse_gare", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["id_agent"], ["users.id_user"], name="fk_caisse_agent", ondelete="RESTRICT"),
        sa.CheckConstraint("statut IN ('OUVERTE', 'CLOTUREE')", name="ck_caisse_statut"),
        sa.CheckConstraint("montant_ouverture >= 0 AND (montant_cloture IS NULL OR montant_cloture >= 0)", name="ck_caisse_montants"),
        sa.CheckConstraint("(statut = 'OUVERTE' AND date_cloture IS NULL) OR (statut = 'CLOTUREE' AND date_cloture IS NOT NULL)", name="ck_caisse_cloture_coherente"),
    )

    op.create_table(
        "operations_caisse",
        sa.Column("id_operation", sa.BigInteger(), sa.Identity(always=True), primary_key=True),
        sa.Column("id_caisse", sa.BigInteger(), nullable=False),
        sa.Column("type_operation", sa.String(20), nullable=False),
        sa.Column("montant", sa.Numeric(12, 2), nullable=False),
        sa.Column("id_paiement", sa.BigInteger()),
        sa.Column("id_cooperative", sa.BigInteger()),
        sa.Column("description", sa.String(255)),
        sa.Column("date_operation", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["id_caisse"], ["caisses.id_caisse"], name="fk_operation_caisse", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["id_paiement"], ["paiements.id_paiement"], name="fk_operation_paiement", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["id_cooperative"], ["cooperatives.id_cooperative"], name="fk_operation_cooperative", ondelete="SET NULL"),
        sa.CheckConstraint("montant > 0", name="ck_operation_montant"),
        sa.CheckConstraint("type_operation IN ('RECETTE', 'DEPENSE', 'COMMISSION')", name="ck_operation_type"),
    )

    op.create_table(
        "notifications",
        sa.Column("id_notification", sa.BigInteger(), sa.Identity(always=True), primary_key=True),
        sa.Column("id_user", sa.BigInteger(), nullable=False),
        sa.Column("type_notification", sa.String(50), nullable=False),
        sa.Column("titre", sa.String(150), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("id_reservation", sa.BigInteger()),
        sa.Column("id_depart", sa.BigInteger()),
        sa.Column("canal", sa.String(20), nullable=False, server_default="PUSH"),
        sa.Column("est_lue", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("date_envoi", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("date_lecture", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["id_user"], ["users.id_user"], name="fk_notification_user", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["id_reservation"], ["reservations.id_reservation"], name="fk_notification_reservation", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["id_depart"], ["departs.id_depart"], name="fk_notification_depart", ondelete="CASCADE"),
        sa.CheckConstraint("canal IN ('PUSH', 'SMS', 'EMAIL')", name="ck_notification_canal"),
        sa.CheckConstraint("type_notification IN ('CONFIRMATION_RESERVATION', 'CONFIRMATION_PAIEMENT', 'RAPPEL_DEPART', 'RETARD', 'ANNULATION', 'MODIFICATION_HORAIRE', 'CONFIRMATION_EMBARQUEMENT', 'EXPIRATION_DOCUMENT')", name="ck_notification_type"),
    )

    index_definitions = {
        "depart_places": (("idx_depart_places_depart", ["id_depart"]), ("idx_depart_places_statut", ["statut"])),
        "reservations": (("idx_reservations_depart", ["id_depart"]), ("idx_reservations_user", ["id_user"]), ("idx_reservations_statut", ["statut"]), ("idx_reservations_expiration", ["date_expiration"])),
        "reservation_places": (("idx_reservation_places_reservation", ["id_reservation"]), ("idx_reservation_places_place", ["id_depart_place"])),
        "billets": (("idx_billets_reservation_place", ["id_reservation_place"]), ("idx_billets_statut", ["statut"]), ("idx_billets_qr_code", ["qr_code_uuid"])),
        "embarquements": (("idx_embarquements_billet", ["id_billet"]), ("idx_embarquements_agent", ["id_agent"]), ("idx_embarquements_statut", ["statut"]), ("idx_embarquements_date", ["date_heure_embarquement"])),
        "paiements": (("idx_paiements_reservation", ["id_reservation"]), ("idx_paiements_statut", ["statut"]), ("idx_paiements_agent", ["id_agent"]), ("idx_paiements_date", ["date_paiement"])),
        "caisses": (("idx_caisses_gare", ["id_gare"]), ("idx_caisses_agent", ["id_agent"]), ("idx_caisses_statut", ["statut"])),
        "operations_caisse": (("idx_operations_caisse_caisse", ["id_caisse"]), ("idx_operations_caisse_type", ["type_operation"]), ("idx_operations_caisse_cooperative", ["id_cooperative"]), ("idx_operations_caisse_date", ["date_operation"])),
        "notifications": (("idx_notifications_user", ["id_user"]), ("idx_notifications_type", ["type_notification"]), ("idx_notifications_lue", ["est_lue"]), ("idx_notifications_date_envoi", ["date_envoi"])),
    }
    for table_name, indexes in index_definitions.items():
        for name, columns in indexes:
            op.create_index(name, table_name, columns)
    op.create_index("uq_embarquement_valide_billet", "embarquements", ["id_billet"], unique=True, postgresql_where=sa.text("statut = 'VALIDE'"))
    op.create_index("uq_caisse_ouverte_gare", "caisses", ["id_gare"], unique=True, postgresql_where=sa.text("statut = 'OUVERTE'"))

    op.execute(sa.text("""
        CREATE OR REPLACE FUNCTION fn_generate_depart_places()
        RETURNS TRIGGER AS $$
        BEGIN
            INSERT INTO depart_places (id_depart, numero_place, statut)
            SELECT NEW.id_depart, gs, 'DISPONIBLE'
            FROM generate_series(1, NEW.nombre_places) AS gs;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        CREATE TRIGGER trg_generate_depart_places
        AFTER INSERT ON departs FOR EACH ROW EXECUTE FUNCTION fn_generate_depart_places();

        INSERT INTO depart_places (id_depart, numero_place, statut)
        SELECT d.id_depart, gs, 'DISPONIBLE'
        FROM departs d CROSS JOIN LATERAL generate_series(1, d.nombre_places) AS gs
        ON CONFLICT (id_depart, numero_place) DO NOTHING;

        CREATE OR REPLACE FUNCTION fn_resize_depart_places()
        RETURNS TRIGGER AS $$
        BEGIN
            IF NEW.nombre_places > OLD.nombre_places THEN
                INSERT INTO depart_places (id_depart, numero_place, statut)
                SELECT NEW.id_depart, gs, 'DISPONIBLE'
                FROM generate_series(OLD.nombre_places + 1, NEW.nombre_places) AS gs;
            ELSIF NEW.nombre_places < OLD.nombre_places THEN
                IF EXISTS (
                    SELECT 1 FROM depart_places
                    WHERE id_depart = NEW.id_depart
                      AND numero_place > NEW.nombre_places
                      AND statut <> 'DISPONIBLE'
                ) THEN
                    RAISE EXCEPTION 'Impossible de réduire la capacité : des places sont déjà utilisées';
                END IF;
                DELETE FROM depart_places
                WHERE id_depart = NEW.id_depart AND numero_place > NEW.nombre_places;
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        CREATE TRIGGER trg_resize_depart_places
        AFTER UPDATE OF nombre_places ON departs FOR EACH ROW EXECUTE FUNCTION fn_resize_depart_places();

        CREATE OR REPLACE FUNCTION fn_reservation_place_lock()
        RETURNS TRIGGER AS $$
        DECLARE v_statut VARCHAR(20); v_depart BIGINT; v_reservation_statut VARCHAR(20);
        BEGIN
            SELECT dp.statut, dp.id_depart, r.statut
            INTO v_statut, v_depart, v_reservation_statut
            FROM depart_places dp
            JOIN reservations r ON r.id_reservation = NEW.id_reservation
            WHERE dp.id_depart_place = NEW.id_depart_place
            FOR UPDATE OF dp;
            IF NOT FOUND THEN RAISE EXCEPTION 'Place ou réservation introuvable'; END IF;
            IF v_depart <> (SELECT id_depart FROM reservations WHERE id_reservation = NEW.id_reservation) THEN
                RAISE EXCEPTION 'La place ne correspond pas au départ de la réservation';
            END IF;
            IF v_reservation_statut <> 'EN_ATTENTE' THEN
                RAISE EXCEPTION 'La réservation n''est plus ouverte';
            END IF;
            IF v_statut <> 'DISPONIBLE' THEN
                RAISE EXCEPTION 'La place n''est plus disponible';
            END IF;
            UPDATE depart_places SET statut = 'RESERVEE', updated_at = CURRENT_TIMESTAMP
            WHERE id_depart_place = NEW.id_depart_place;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        CREATE TRIGGER trg_reservation_place_lock
        BEFORE INSERT ON reservation_places FOR EACH ROW EXECUTE FUNCTION fn_reservation_place_lock();

        CREATE OR REPLACE FUNCTION fn_reservation_release_places()
        RETURNS TRIGGER AS $$
        BEGIN
            IF NEW.statut IN ('ANNULEE', 'EXPIREE') AND OLD.statut NOT IN ('ANNULEE', 'EXPIREE') THEN
                UPDATE depart_places SET statut = 'DISPONIBLE', updated_at = CURRENT_TIMESTAMP
                WHERE statut = 'RESERVEE' AND id_depart_place IN (
                    SELECT id_depart_place FROM reservation_places WHERE id_reservation = NEW.id_reservation
                );
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        CREATE TRIGGER trg_reservation_release_places
        AFTER UPDATE OF statut ON reservations FOR EACH ROW EXECUTE FUNCTION fn_reservation_release_places();

        CREATE OR REPLACE FUNCTION fn_sync_depart_places_count()
        RETURNS TRIGGER AS $$
        DECLARE v_depart BIGINT;
        BEGIN
            v_depart := COALESCE(NEW.id_depart, OLD.id_depart);
            UPDATE departs SET places_reservees = (
                SELECT COUNT(*) FROM depart_places
                WHERE id_depart = v_depart AND statut <> 'DISPONIBLE'
            ), updated_at = CURRENT_TIMESTAMP WHERE id_depart = v_depart;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        CREATE TRIGGER trg_sync_depart_places_count
        AFTER INSERT OR UPDATE OF statut ON depart_places FOR EACH ROW EXECUTE FUNCTION fn_sync_depart_places_count();

        CREATE OR REPLACE FUNCTION fn_embarquement_valide()
        RETURNS TRIGGER AS $$
        DECLARE v_place BIGINT; v_reservation BIGINT;
        BEGIN
            IF NEW.statut = 'VALIDE' THEN
                SELECT rp.id_depart_place, rp.id_reservation INTO v_place, v_reservation
                FROM billets b JOIN reservation_places rp ON rp.id_reservation_place = b.id_reservation_place
                WHERE b.id_billet = NEW.id_billet;
                UPDATE billets SET statut = 'UTILISE', date_utilisation = NEW.date_heure_embarquement, updated_at = CURRENT_TIMESTAMP
                WHERE id_billet = NEW.id_billet;
                UPDATE depart_places SET statut = 'OCCUPEE', updated_at = CURRENT_TIMESTAMP
                WHERE id_depart_place = v_place;
                UPDATE reservations SET statut = 'EMBARQUEE', updated_at = CURRENT_TIMESTAMP
                WHERE id_reservation = v_reservation AND statut IN ('CONFIRMEE', 'PAYEE');
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        CREATE TRIGGER trg_embarquement_valide
        AFTER INSERT ON embarquements FOR EACH ROW EXECUTE FUNCTION fn_embarquement_valide();

        CREATE OR REPLACE FUNCTION fn_paiement_maj_reservation()
        RETURNS TRIGGER AS $$
        BEGIN
            IF NEW.statut = 'VALIDE' THEN
                UPDATE reservations SET statut = 'PAYEE', updated_at = CURRENT_TIMESTAMP
                WHERE id_reservation = NEW.id_reservation AND statut IN ('EN_ATTENTE', 'CONFIRMEE');
            ELSIF NEW.statut = 'REMBOURSE' THEN
                UPDATE reservations SET statut = 'ANNULEE', updated_at = CURRENT_TIMESTAMP
                WHERE id_reservation = NEW.id_reservation AND statut NOT IN ('ANNULEE', 'EXPIREE', 'TERMINEE');
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        CREATE TRIGGER trg_paiement_maj_reservation
        AFTER INSERT OR UPDATE OF statut ON paiements FOR EACH ROW EXECUTE FUNCTION fn_paiement_maj_reservation();
    """))

    op.execute(sa.text("""
        CREATE VIEW v_billets_details AS
        SELECT b.id_billet, b.numero_billet, b.qr_code_uuid, b.statut AS statut_billet,
               b.date_emission, b.date_utilisation, r.id_reservation, r.numero_reservation,
               r.statut AS statut_reservation, r.id_user, rp.nom_passager, rp.telephone_passager,
               dp.numero_place, d.id_depart, d.date_depart, d.heure_depart, d.statut AS statut_depart,
               t.prix, t.devise, dest_dep.nom AS destination_depart, dest_arr.nom AS destination_arrivee,
               v.immatriculation, c.nom AS nom_cooperative
        FROM billets b
        JOIN reservation_places rp ON rp.id_reservation_place = b.id_reservation_place
        JOIN reservations r ON r.id_reservation = rp.id_reservation
        JOIN depart_places dp ON dp.id_depart_place = rp.id_depart_place
        JOIN departs d ON d.id_depart = dp.id_depart
        JOIN itineraires i ON i.id_itineraire = d.id_itineraire
        JOIN destinations dest_dep ON dest_dep.id_destination = i.id_destination_depart
        JOIN destinations dest_arr ON dest_arr.id_destination = i.id_destination_arrivee
        JOIN vehicules v ON v.id_vehicule = d.id_vehicule
        JOIN cooperatives c ON c.id_cooperative = d.id_cooperative
        JOIN tarifs t ON t.id_tarif = d.id_tarif;

        CREATE VIEW v_departs_du_jour AS
        SELECT d.id_depart, d.date_depart, d.heure_depart, d.statut, d.nombre_places,
               d.places_reservees, d.nombre_places - d.places_reservees AS places_disponibles,
               ROUND((d.places_reservees::NUMERIC / NULLIF(d.nombre_places, 0)) * 100, 2) AS taux_remplissage_pct,
               c.nom AS cooperative, v.immatriculation, dest_dep.nom AS destination_depart,
               dest_arr.nom AS destination_arrivee
        FROM departs d JOIN cooperatives c ON c.id_cooperative = d.id_cooperative
        JOIN vehicules v ON v.id_vehicule = d.id_vehicule
        JOIN itineraires i ON i.id_itineraire = d.id_itineraire
        JOIN destinations dest_dep ON dest_dep.id_destination = i.id_destination_depart
        JOIN destinations dest_arr ON dest_arr.id_destination = i.id_destination_arrivee
        WHERE d.date_depart = CURRENT_DATE;

        CREATE VIEW v_recettes_par_jour AS
        SELECT DATE(oc.date_operation) AS jour,
               COALESCE(SUM(oc.montant) FILTER (WHERE oc.type_operation = 'RECETTE'), 0) AS total_recettes,
               COALESCE(SUM(oc.montant) FILTER (WHERE oc.type_operation = 'DEPENSE'), 0) AS total_depenses,
               COALESCE(SUM(oc.montant) FILTER (WHERE oc.type_operation = 'COMMISSION'), 0) AS total_commissions
        FROM operations_caisse oc GROUP BY DATE(oc.date_operation) ORDER BY jour DESC;

        CREATE VIEW v_statistiques_destinations AS
        SELECT dest_arr.id_destination, dest_arr.nom AS destination, COUNT(r.id_reservation) AS nombre_reservations
        FROM reservations r JOIN departs d ON d.id_depart = r.id_depart
        JOIN itineraires i ON i.id_itineraire = d.id_itineraire
        JOIN destinations dest_arr ON dest_arr.id_destination = i.id_destination_arrivee
        WHERE r.statut NOT IN ('ANNULEE', 'EXPIREE')
        GROUP BY dest_arr.id_destination, dest_arr.nom;

        CREATE VIEW v_statistiques_annulations_retards AS
        SELECT d.date_depart AS jour,
               COUNT(*) FILTER (WHERE d.statut = 'ANNULE') AS nombre_annulations,
               COUNT(*) FILTER (WHERE d.statut = 'RETARDE') AS nombre_retards,
               COUNT(*) AS nombre_departs_total
        FROM departs d GROUP BY d.date_depart ORDER BY d.date_depart DESC;
    """))


def downgrade() -> None:
    for view in ("v_statistiques_annulations_retards", "v_statistiques_destinations", "v_recettes_par_jour", "v_departs_du_jour", "v_billets_details"):
        op.execute(f"DROP VIEW IF EXISTS {view}")
    op.execute("DROP TRIGGER IF EXISTS trg_paiement_maj_reservation ON paiements")
    op.execute("DROP TRIGGER IF EXISTS trg_embarquement_valide ON embarquements")
    op.execute("DROP TRIGGER IF EXISTS trg_sync_depart_places_count ON depart_places")
    op.execute("DROP TRIGGER IF EXISTS trg_reservation_release_places ON reservations")
    op.execute("DROP TRIGGER IF EXISTS trg_reservation_place_lock ON reservation_places")
    op.execute("DROP TRIGGER IF EXISTS trg_resize_depart_places ON departs")
    op.execute("DROP TRIGGER IF EXISTS trg_generate_depart_places ON departs")
    for function in (
        "fn_paiement_maj_reservation", "fn_embarquement_valide", "fn_sync_depart_places_count",
        "fn_reservation_release_places", "fn_reservation_place_lock", "fn_resize_depart_places",
        "fn_generate_depart_places",
    ):
        op.execute(f"DROP FUNCTION IF EXISTS {function}()")
    for table in ("notifications", "operations_caisse", "caisses", "paiements", "embarquements", "billets", "reservation_places", "reservations", "depart_places"):
        op.drop_table(table)
