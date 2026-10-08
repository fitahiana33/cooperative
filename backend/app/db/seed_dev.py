"""Fill every table with coherent demo data, optionally wiping the database first.

Run from ``backend/`` (or inside the backend container)::

    python -m app.db.seed_dev                  # seed an empty database
    python -m app.db.seed_dev --reset          # wipe every table, then seed
    python -m app.db.seed_dev --reset --empty  # wipe, keep only roles/permissions/admin

Dates are generated around today so the dashboards always show finished,
ongoing and upcoming departures. Bookings go through the same states as the
application (EN_ATTENTE -> CONFIRMEE -> PAYEE -> EMBARQUEE) so the PostgreSQL
triggers keep seats, tickets and counters consistent.
"""

from __future__ import annotations

import argparse
import random
import sys
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

import qrcode
from sqlalchemy import func, select, text, update
from sqlalchemy.orm import Session

import app.models  # noqa: F401 - registers every table on Base.metadata
from app.core.config import settings
from app.db.base import Base
from app.db.seed import seed_default_admin
from app.db.session import SessionLocal
from app.models import (
    Billet,
    BilletStatus,
    Caisse,
    CaisseStatus,
    Chauffeur,
    Cooperative,
    CooperativeMember,
    Depart,
    DepartPlace,
    DepartPlaceStatus,
    DepartStatus,
    Destination,
    Embarquement,
    EmbarquementStatus,
    Emplacement,
    Gare,
    GareAgent,
    GareCooperative,
    Itineraire,
    ItineraireCooperative,
    Marque,
    Modele,
    Notification,
    NotificationChannel,
    NotificationType,
    OperationCaisse,
    OperationType,
    Paiement,
    PaiementMethode,
    PaiementStatus,
    Quai,
    Reservation,
    ReservationPlace,
    ReservationStatus,
    RevokedToken,
    Role,
    Tarif,
    User,
    Vehicule,
    VehiculeChauffeur,
    VehiculeDocument,
    Zone,
)
from app.models.user import UserRole
from app.services.authentication.password import hash_password

DEMO_PASSWORD = "Demo123!"
EMAIL_DOMAIN = "cooperative.com"
LOCAL_TZ = timezone(timedelta(hours=3))  # Madagascar, no daylight saving
PAST_DAYS = 10
FUTURE_DAYS = 7
DESK_OPEN, DESK_CLOSE = time(6, 0), time(19, 0)
LAST_DESK_EVENT = time(18, 30)

FIRST_NAMES = [
    "Hery", "Fanja", "Tiana", "Mamy", "Lova", "Nirina", "Fara", "Andry", "Haingo", "Tojo",
    "Voahirana", "Rivo", "Nomena", "Mialy", "Toky", "Sitraka", "Fitia", "Onja", "Hasina",
    "Faniry", "Rado", "Zo", "Aina", "Volatiana", "Njaka", "Miora", "Tsiry", "Holy",
]
LAST_NAMES = [
    "Rakoto", "Rabe", "Randrianarisoa", "Rasolofonirina", "Andriamanantena", "Razafindrakoto",
    "Rakotomalala", "Ravelonjanahary", "Ramanantsoa", "Rasoanaivo", "Andrianjafy", "Rajaonarison",
    "Razanamparany", "Ratsimbazafy", "Rabemananjara", "Rakotondrabe", "Randriamampianina",
    "Raharison", "Rafanomezantsoa", "Ravoahangy",
]

# (nom, region, description, is_active)
DESTINATIONS = [
    ("Antananarivo", "Analamanga", "Capitale, point de départ des routes nationales.", True),
    ("Toamasina", "Atsinanana", "Premier port du pays, au bout de la RN2.", True),
    ("Moramanga", "Alaotra-Mangoro", "Carrefour entre la RN2 et la RN44.", True),
    ("Antsirabe", "Vakinankaratra", "Ville d'eau des Hautes Terres, sur la RN7.", True),
    ("Ambositra", "Amoron'i Mania", "Capitale de l'artisanat zafimaniry.", True),
    ("Fianarantsoa", "Haute Matsiatra", "Ville universitaire du Sud, sur la RN7.", True),
    ("Mahajanga", "Boeny", "Port de la côte nord-ouest, au bout de la RN4.", True),
    ("Toliara", "Atsimo-Andrefana", "Terminus de la RN7 dans le Sud-Ouest.", True),
    ("Antsiranana", "Diana", "Grande ville du Nord.", True),
    ("Morondava", "Menabe", "Ville côtière de l'Ouest, desserte suspendue.", False),
]

# (ville A, ville B, distance km, durée minutes, prix général MGA, actif) - served both ways
ROUTES = [
    ("Antananarivo", "Toamasina", 353, 480, 35000, True),
    ("Antananarivo", "Moramanga", 113, 150, 12000, True),
    ("Antananarivo", "Antsirabe", 169, 240, 15000, True),
    ("Antananarivo", "Ambositra", 259, 360, 22000, True),
    ("Antananarivo", "Fianarantsoa", 408, 600, 35000, True),
    ("Antananarivo", "Mahajanga", 568, 720, 45000, True),
    ("Antsirabe", "Fianarantsoa", 240, 360, 20000, True),
    ("Fianarantsoa", "Toliara", 510, 720, 45000, True),
    ("Antananarivo", "Antsiranana", 1080, 1500, 90000, False),
]
ROUTES_WITH_PRICE_HISTORY = {("Antananarivo", "Toamasina"), ("Antananarivo", "Antsirabe"), ("Fianarantsoa", "Toliara")}

# (slug, nom, ville, region, adresse, latitude, longitude)
GARES = [
    ("ampasampito", "Gare routière d'Ampasampito", "Antananarivo", "Analamanga", "Ampasampito, Antananarivo 101", -18.8985, 47.5432),
    ("fasankarana", "Gare routière de Fasan'ny Karana", "Antananarivo", "Analamanga", "Anosizato, Antananarivo 102", -18.9312, 47.5050),
    ("ambodivona", "Gare routière du Nord", "Antananarivo", "Analamanga", "Ambodivona, Antananarivo 101", -18.8935, 47.5280),
    ("toamasina", "Gare routière de Toamasina", "Toamasina", "Atsinanana", "Boulevard de l'OUA, Toamasina 501", -18.1492, 49.4023),
    ("moramanga", "Gare routière de Moramanga", "Moramanga", "Alaotra-Mangoro", "RN2, Moramanga 514", -18.9476, 48.2300),
    ("antsirabe", "Gare routière d'Antsirabe", "Antsirabe", "Vakinankaratra", "Avenue de l'Indépendance, Antsirabe 110", -19.8659, 47.0333),
    ("ambositra", "Gare routière d'Ambositra", "Ambositra", "Amoron'i Mania", "RN7, Ambositra 306", -20.5310, 47.2440),
    ("fianarantsoa", "Gare routière de Fianarantsoa", "Fianarantsoa", "Haute Matsiatra", "Antanifotsy, Fianarantsoa 301", -21.4527, 47.0857),
    ("mahajanga", "Gare routière de Mahajanga", "Mahajanga", "Boeny", "Avenue Philibert Tsiranana, Mahajanga 401", -15.7167, 46.3167),
    ("toliara", "Gare routière de Toliara", "Toliara", "Atsimo-Andrefana", "Route de l'aéroport, Toliara 601", -23.3568, 43.6917),
]
# Antananarivo has one station per direction.
TANA_GARE_BY_DESTINATION = {
    "Toamasina": "ampasampito", "Moramanga": "ampasampito",
    "Antsirabe": "fasankarana", "Ambositra": "fasankarana", "Fianarantsoa": "fasankarana",
    "Mahajanga": "ambodivona", "Antsiranana": "ambodivona",
}

# (sigle, nom, ville, routes servies)
COOPERATIVES = [
    ("FTE", "Fitahiana Express", "Antananarivo", [("Antananarivo", "Toamasina"), ("Antananarivo", "Moramanga"), ("Antananarivo", "Mahajanga")]),
    ("MDT", "Mendrika Trans", "Antsirabe", [("Antananarivo", "Antsirabe"), ("Antananarivo", "Ambositra"), ("Antsirabe", "Fianarantsoa")]),
    ("SMR", "Soamiray Transport", "Fianarantsoa", [("Antananarivo", "Fianarantsoa"), ("Fianarantsoa", "Toliara"), ("Antananarivo", "Antsirabe")]),
    ("ZAV", "Zotra Avaratra", "Mahajanga", [("Antananarivo", "Mahajanga"), ("Antananarivo", "Toamasina")]),
]
# Cooperative-specific fares, applied in both directions.
COOPERATIVE_FARES = {
    ("FTE", "Antananarivo", "Toamasina"): 40000,
    ("ZAV", "Antananarivo", "Mahajanga"): 42000,
    ("MDT", "Antananarivo", "Ambositra"): 24000,
}

# (marque, modèle, places, chevaux)
MODELS = {
    "sprinter515": ("Mercedes-Benz", "Sprinter 515", 22, 150),
    "sprinter313": ("Mercedes-Benz", "Sprinter 313", 18, 130),
    "hiace": ("Toyota", "HiAce", 15, 136),
    "coaster": ("Toyota", "Coaster", 29, 150),
    "county": ("Hyundai", "County", 25, 140),
    "civilian": ("Nissan", "Civilian", 26, 175),
}
INACTIVE_BRAND = ("Renault", "Master", "Modèle retiré de la flotte.")

# (sigle, modèle, route, heure de départ, état); vehicles with a route run daily, alternating direction.
FLEET = [
    ("FTE", "sprinter515", ("Antananarivo", "Toamasina"), time(7, 0), "BON_ETAT"),
    ("FTE", "hiace", ("Antananarivo", "Toamasina"), time(13, 0), "BON_ETAT"),
    ("FTE", "sprinter313", ("Antananarivo", "Moramanga"), time(8, 30), "MOYEN"),
    ("FTE", "coaster", ("Antananarivo", "Mahajanga"), time(17, 0), "BON_ETAT"),
    ("MDT", "sprinter313", ("Antananarivo", "Antsirabe"), time(6, 30), "BON_ETAT"),
    ("MDT", "hiace", ("Antananarivo", "Ambositra"), time(7, 30), "BON_ETAT"),
    ("MDT", "county", ("Antsirabe", "Fianarantsoa"), time(9, 0), "MOYEN"),
    ("MDT", "sprinter515", None, None, "A_REPARER"),
    ("SMR", "civilian", ("Antananarivo", "Fianarantsoa"), time(6, 0), "BON_ETAT"),
    ("SMR", "county", ("Fianarantsoa", "Toliara"), time(16, 0), "BON_ETAT"),
    ("SMR", "hiace", ("Antananarivo", "Antsirabe"), time(14, 0), "BON_ETAT"),
    ("SMR", "hiace", None, None, "HORS_SERVICE"),
    ("ZAV", "coaster", ("Antananarivo", "Mahajanga"), time(18, 0), "BON_ETAT"),
    ("ZAV", "sprinter515", ("Antananarivo", "Toamasina"), time(19, 30), "BON_ETAT"),
]

REFUSAL_REASONS = [
    "Billet présenté pour un autre départ.",
    "Nom du passager différent de la pièce d'identité.",
    "Passager arrivé après la fermeture de l'embarquement.",
]

# Booking outcomes per departure status, as (outcome, weight).
OUTCOMES = {
    DepartStatus.TERMINE: [("TERMINEE", 78), ("NO_SHOW", 4), ("EXPIREE", 8), ("ANNULEE", 5), ("REMBOURSEE", 5)],
    DepartStatus.ANNULE: [("REMBOURSEE", 60), ("ANNULEE", 40)],
    DepartStatus.PARTI: [("EMBARQUEE", 85), ("PAYEE", 5), ("EXPIREE", 5), ("ANNULEE", 5)],
    DepartStatus.EMBARQUEMENT: [("EMBARQUEE", 45), ("PAYEE", 35), ("CONFIRMEE", 10), ("EXPIREE", 5), ("ANNULEE", 5)],
    DepartStatus.RETARDE: [("EMBARQUEE", 30), ("PAYEE", 50), ("CONFIRMEE", 10), ("EXPIREE", 5), ("ANNULEE", 5)],
    DepartStatus.PROGRAMME: [("EN_ATTENTE", 10), ("CONFIRMEE", 25), ("PAYEE", 45), ("EXPIREE", 8), ("ANNULEE", 5), ("REMBOURSEE", 7)],
}


@dataclass
class DepartContext:
    depart: Depart
    label: str
    dep_at: datetime
    arr_at: datetime
    gare: Gare
    agent: User
    prix: Decimal
    bookings: list[tuple[int, User, str]] = field(default_factory=list)


class DemoSeeder:
    def __init__(self, db: Session, rng: random.Random, *, write_qr: bool = True):
        self.db = db
        self.rng = rng
        self.write_qr = write_qr
        self.now = datetime.now(LOCAL_TZ).replace(microsecond=0)
        self.today = self.now.date()
        self.password_hash = hash_password(DEMO_PASSWORD)
        self.qr_dir = settings.uploads_dir / "qr_codes"
        self.qr_dir.mkdir(parents=True, exist_ok=True)
        self.roles = {role.libelle: role for role in db.scalars(select(Role))}
        self.caisses: dict[tuple[int, date], Caisse] = {}
        self.pending_expiry_alerts: list[tuple[Cooperative, str]] = []
        self.pending_by_user: dict[int, int] = {}

    # ------------------------------------------------------------------ helpers

    def at(self, day: date, moment: time) -> datetime:
        return datetime.combine(day, moment, LOCAL_TZ)

    def person(self) -> tuple[str, str]:
        return self.rng.choice(FIRST_NAMES), self.rng.choice(LAST_NAMES)

    def phone(self) -> str:
        r = self.rng
        return f"+261 {r.choice(['32', '33', '34', '38'])} {r.randint(10, 99)} {r.randint(100, 999)} {r.randint(10, 99)}"

    def pick(self, weighted: list[tuple[str, int]]) -> str:
        values, weights = zip(*weighted)
        return self.rng.choices(values, weights)[0]

    def between(self, start: datetime, end: datetime) -> datetime:
        return start + (end - start) * self.rng.random()

    def desk_time(self, start: datetime, end: datetime) -> datetime | None:
        """Random moment between start and end that falls within cash-desk hours."""
        day = end.date()
        while day >= start.date():
            low = max(start, self.at(day, DESK_OPEN))
            high = min(end, self.at(day, LAST_DESK_EVENT))
            if low < high:
                return self.between(low, high).replace(microsecond=0)
            day -= timedelta(days=1)
        return None

    def user(self, email_prefix: str, role: str, *, first: str | None = None, last: str | None = None,
             address: str | None = None, is_active: bool = True) -> User:
        if first is None or last is None:
            first, last = self.person()
        created_at = self.now - timedelta(days=self.rng.randint(30, 400))
        item = User(
            name=last,
            first_name=first,
            email=f"{email_prefix}@{EMAIL_DOMAIN}",
            telephone=self.phone(),
            address=address,
            password_hash=self.password_hash,
            is_active=is_active,
            created_at=created_at,
            last_login_at=self.now - timedelta(hours=self.rng.randint(1, 240)) if is_active else None,
        )
        item.roles.append(self.roles[role])
        self.db.add(item)
        return item

    def notify(self, user: User, type_: str, titre: str, message: str, sent_at: datetime, *,
               reservation_id: int | None = None, depart_id: int | None = None) -> None:
        sent_at = min(sent_at, self.now)
        read = sent_at < self.now - timedelta(days=1) and self.rng.random() < 0.8
        self.db.add(Notification(
            id_user=user.id,
            type_notification=type_,
            titre=titre,
            message=message,
            id_reservation=reservation_id,
            id_depart=depart_id,
            canal=self.pick([(NotificationChannel.PUSH, 70), (NotificationChannel.SMS, 20), (NotificationChannel.EMAIL, 10)]),
            est_lue=read,
            date_envoi=sent_at,
            date_lecture=sent_at + timedelta(minutes=self.rng.randint(1, 600)) if read else None,
            created_at=sent_at,
        ))

    def caisse(self, gare: Gare, agent: User, moment: datetime) -> Caisse:
        day = moment.astimezone(LOCAL_TZ).date()
        key = (gare.id, day)
        if key not in self.caisses:
            opened_at = self.at(day, DESK_OPEN) - timedelta(minutes=15)
            item = Caisse(
                id_gare=gare.id,
                id_agent=agent.id,
                date_ouverture=min(opened_at, self.now),
                montant_ouverture=Decimal(self.rng.choice([50000, 100000, 150000])),
                statut=CaisseStatus.OUVERTE if day == self.today else CaisseStatus.CLOTUREE,
                date_cloture=None if day == self.today else self.at(day, DESK_CLOSE),
                created_at=min(opened_at, self.now),
            )
            self.db.add(item)
            self.db.flush()
            self.caisses[key] = item
        return self.caisses[key]

    def set_reservation_status(self, reservation: Reservation, statut: str, moment: datetime) -> None:
        # Statements rather than ORM attributes: triggers also change these rows.
        self.db.execute(update(Reservation).where(Reservation.id == reservation.id).values(statut=statut, updated_at=moment))

    def set_billets_status(self, billets: list[Billet], statut: str, moment: datetime) -> None:
        ids = [billet.id for billet in billets]
        self.db.execute(update(Billet).where(Billet.id.in_(ids)).values(statut=statut, updated_at=moment))

    # ------------------------------------------------------------------ seeding steps

    def run(self) -> None:
        self.seed_people_and_stations()
        self.seed_routes()
        self.seed_fleet()
        self.seed_departures()
        self.close_cash_desks()
        self.seed_misc()

    def seed_people_and_stations(self) -> None:
        db = self.db
        self.gares: dict[str, Gare] = {}
        for slug, nom, ville, region, adresse, lat, lon in GARES:
            gare = Gare(
                nom=nom, adresse=adresse, ville=ville, region=region, telephone=self.phone(),
                email=f"gare.{slug}@{EMAIL_DOMAIN}", description=f"Gare routière desservant {ville} et sa région.",
                latitude=Decimal(str(lat)), longitude=Decimal(str(lon)),
            )
            db.add(gare)
            self.gares[slug] = gare
        db.flush()

        for slug, gare in self.gares.items():
            quai_count = 5 if gare.ville == "Antananarivo" else 3
            for n in range(1, quai_count + 1):
                db.add(Quai(id_gare=gare.id, numero=f"Q{n}", nom=f"Quai {n}", is_active=not (slug == "moramanga" and n == quai_count)))
            zones = {
                "DEPART": Zone(id_gare=gare.id, nom="Zone de départ", type_zone="DEPART", description="Aire de chargement des véhicules."),
                "PARKING": Zone(id_gare=gare.id, nom="Parking", type_zone="PARKING", description="Stationnement des véhicules en attente."),
                "GUICHET": Zone(id_gare=gare.id, nom="Guichets", type_zone="GUICHET", description="Guichets des coopératives."),
                "ATTENTE": Zone(id_gare=gare.id, nom="Salle d'attente", type_zone="ATTENTE", description="Espace passagers."),
            }
            db.add_all(zones.values())
            db.flush()
            for n in range(1, 5):
                db.add(Emplacement(id_zone=zones["DEPART"].id, code=f"D{n:02d}", nom=f"Aire {n}", type_emplacement="CHARGEMENT", is_available=self.rng.random() < 0.6))
            for n in range(1, 9):
                db.add(Emplacement(id_zone=zones["PARKING"].id, code=f"P{n:02d}", nom=f"Place {n}", type_emplacement="STATIONNEMENT", is_available=self.rng.random() < 0.7))
            for n in range(1, 4):
                db.add(Emplacement(id_zone=zones["GUICHET"].id, code=f"G{n:02d}", nom=f"Guichet {n}", type_emplacement="GUICHET", is_available=n == 3))
            db.add(Emplacement(id_zone=zones["ATTENTE"].id, code="A01", nom="Bancs passagers", type_emplacement="ATTENTE", is_active=slug != "toliara"))

        self.responsables_gare = [self.user(f"responsable.gare{n}", UserRole.RESPONSABLE_GARE) for n in (1, 2)]
        self.agents = {slug: self.user(f"agent.{slug}", UserRole.AGENT_GARE) for slug in self.gares}
        self.passengers = [self.user(f"passager{n:02d}", UserRole.PASSAGER, address=f"Lot {self.rng.randint(1, 300)} {self.rng.choice(['Analakely', 'Isotry', 'Ankorondrano', 'Ambohijatovo', 'Tsaralalana'])}") for n in range(1, 26)]
        self.passengers.append(self.user("passager.inactif", UserRole.PASSAGER, is_active=False))
        db.flush()
        self.active_passengers = [p for p in self.passengers if p.is_active]

        self.cooperatives: dict[str, Cooperative] = {}
        self.coop_responsables: dict[str, User] = {}
        joined = self.today - timedelta(days=365)
        for n, (sigle, nom, ville, _) in enumerate(COOPERATIVES, start=1):
            responsable = self.user(f"responsable.{sigle.lower()}", UserRole.RESPONSABLE_COOPERATIVE)
            db.flush()
            coop = Cooperative(
                nom=f"Coopérative {nom}", sigle=sigle, numero_agrement=f"AGR-{self.today.year - 3}-{n:04d}",
                adresse=f"Gare routière, {ville}", ville=ville, telephone=self.phone(),
                email=f"contact.{sigle.lower()}@{EMAIL_DOMAIN}",
                description=f"Coopérative de transport de voyageurs basée à {ville}.",
                responsable_id=responsable.id,
            )
            db.add(coop)
            db.flush()
            db.add(CooperativeMember(id_cooperative=coop.id, id_user=responsable.id, fonction="Responsable", date_adhesion=joined))
            self.cooperatives[sigle] = coop
            self.coop_responsables[sigle] = responsable

        # Stations each cooperative operates from: every route end, both directions are served.
        linked: set[tuple[str, str]] = set()
        for sigle, _, _, routes in COOPERATIVES:
            for a, b in routes:
                linked.add((sigle, self.origin_gare_slug(a, b)))
                linked.add((sigle, self.origin_gare_slug(b, a)))
        for sigle, slug in sorted(linked):
            db.add(GareCooperative(id_gare=self.gares[slug].id, id_cooperative=self.cooperatives[sigle].id, date_debut=joined))
        # Each agent works at one station and sees the cooperatives operating there.
        for slug, agent in self.agents.items():
            db.add(GareAgent(id_gare=self.gares[slug].id, id_user=agent.id))
        # A former partnership kept for history.
        db.add(GareCooperative(id_gare=self.gares["toliara"].id, id_cooperative=self.cooperatives["FTE"].id,
                               date_debut=joined - timedelta(days=365), date_fin=joined, is_active=False))
        db.flush()

    def origin_gare_slug(self, origin: str, destination: str) -> str:
        if origin == "Antananarivo":
            return TANA_GARE_BY_DESTINATION[destination]
        return next(slug for slug, _, ville, *_ in GARES if ville == origin)

    def seed_routes(self) -> None:
        db = self.db
        self.destinations = {}
        for nom, region, description, is_active in DESTINATIONS:
            item = Destination(nom=nom, region=region, description=description, is_active=is_active)
            db.add(item)
            self.destinations[nom] = item
        db.flush()

        self.itineraires: dict[tuple[str, str], Itineraire] = {}
        self.route_info: dict[tuple[str, str], tuple[int, int]] = {}
        tarif_start = self.today - timedelta(days=120)
        for a, b, km, minutes, prix, is_active in ROUTES:
            for origin, destination in ((a, b), (b, a)):
                item = Itineraire(
                    id_destination_depart=self.destinations[origin].id,
                    id_destination_arrivee=self.destinations[destination].id,
                    distance_km=Decimal(km), duree_estimee_minutes=minutes,
                    description=f"{origin} - {destination} par la route nationale.",
                    is_active=is_active,
                )
                db.add(item)
                db.flush()
                self.itineraires[(origin, destination)] = item
                self.route_info[(origin, destination)] = (minutes, prix)
                db.add(Tarif(id_itineraire=item.id, prix=Decimal(prix), date_debut=tarif_start))
                if (a, b) in ROUTES_WITH_PRICE_HISTORY:
                    db.add(Tarif(id_itineraire=item.id, prix=Decimal(round(prix * 0.9, -3)),
                                 date_debut=self.today - timedelta(days=400), date_fin=tarif_start - timedelta(days=1), is_active=False))
        for (sigle, a, b), prix in COOPERATIVE_FARES.items():
            for key in ((a, b), (b, a)):
                db.add(Tarif(id_itineraire=self.itineraires[key].id, id_cooperative=self.cooperatives[sigle].id,
                             prix=Decimal(prix), date_debut=tarif_start))

        joined = self.today - timedelta(days=365)
        for sigle, _, _, routes in COOPERATIVES:
            for a, b in routes:
                for key in ((a, b), (b, a)):
                    db.add(ItineraireCooperative(id_itineraire=self.itineraires[key].id, id_cooperative=self.cooperatives[sigle].id, date_debut=joined))
        for key in (("Antananarivo", "Antsiranana"), ("Antsiranana", "Antananarivo")):
            db.add(ItineraireCooperative(id_itineraire=self.itineraires[key].id, id_cooperative=self.cooperatives["ZAV"].id,
                                         date_debut=joined - timedelta(days=200), date_fin=joined, is_active=False))
        db.flush()

        self.tarifs: dict[tuple[str, tuple[str, str]], Tarif] = {}
        for tarif in db.scalars(select(Tarif).where(Tarif.is_active.is_(True))):
            route = next(key for key, it in self.itineraires.items() if it.id == tarif.id_itineraire)
            sigle = next((s for s, c in self.cooperatives.items() if c.id == tarif.id_cooperative), None)
            self.tarifs[(sigle, route)] = tarif

    def seed_fleet(self) -> None:
        db = self.db
        marques = {}
        modeles = {}
        for key, (marque_nom, modele_nom, _, _) in MODELS.items():
            if marque_nom not in marques:
                marques[marque_nom] = Marque(nom=marque_nom, description=f"Véhicules {marque_nom}.")
                db.add(marques[marque_nom])
                db.flush()
            modeles[key] = Modele(id_marque=marques[marque_nom].id, nom=modele_nom, description=f"{marque_nom} {modele_nom}")
            db.add(modeles[key])
        retired = Marque(nom=INACTIVE_BRAND[0], description=INACTIVE_BRAND[2], is_active=False)
        db.add(retired)
        db.flush()
        db.add(Modele(id_marque=retired.id, nom=INACTIVE_BRAND[1], is_active=False))
        db.flush()

        self.operational: list[tuple[Vehicule, Chauffeur, str, tuple[str, str], time]] = []
        plates = self.rng.sample(range(1000, 9999), len(FLEET))
        assigned_since = self.today - timedelta(days=180)
        driver_number = 0
        for index, (sigle, model_key, route, hour, etat) in enumerate(FLEET):
            _, _, places, chevaux = MODELS[model_key]
            coop = self.cooperatives[sigle]
            running = route is not None
            vehicule = Vehicule(
                id_modele=modeles[model_key].id, id_cooperative=coop.id,
                immatriculation=f"{plates[index]} T{self.rng.choice('ABCDEFGH')}{self.rng.choice('ABCDEFGH')}",
                chevaux=chevaux, nombre_places=places, disponibilite=running, etat=etat,
                description=None if running else "Immobilisé au garage de la coopérative.",
                is_active=etat != "HORS_SERVICE",
            )
            db.add(vehicule)
            db.flush()
            self.add_vehicle_documents(vehicule, expired=not running)
            if running:
                driver_number += 1
                chauffeur = self.chauffeur(driver_number, coop)
                db.flush()
                db.add(VehiculeChauffeur(id_vehicule=vehicule.id, id_chauffeur=chauffeur.id, date_debut=assigned_since))
                self.operational.append((vehicule, chauffeur, sigle, route, hour))
            elif etat == "HORS_SERVICE":
                # Its former driver is now without vehicle and with an expired licence.
                driver_number += 1
                chauffeur = self.chauffeur(driver_number, coop, permis_expire=True)
                db.flush()
                db.add(VehiculeChauffeur(id_vehicule=vehicule.id, id_chauffeur=chauffeur.id, date_debut=self.today - timedelta(days=400),
                                         date_fin=self.today - timedelta(days=60), is_active=False))
        driver_number += 1
        self.chauffeur(driver_number, self.cooperatives["MDT"], disponible=False)
        db.flush()

    def chauffeur(self, number: int, coop: Cooperative, *, permis_expire: bool = False, disponible: bool = True) -> Chauffeur:
        user = self.user(f"chauffeur{number:02d}", UserRole.CHAUFFEUR)
        self.db.flush()
        self.db.add(CooperativeMember(id_cooperative=coop.id, id_user=user.id, fonction="Chauffeur", date_adhesion=self.today - timedelta(days=300)))
        expiration = self.today - timedelta(days=45) if permis_expire else self.today + timedelta(days=self.rng.randint(200, 1400))
        item = Chauffeur(id_user=user.id, id_cooperative=coop.id, numero_permis=f"MG-PC-{100000 + number * 7919}",
                         categorie_permis="D", date_expiration_permis=expiration, disponibilite=disponible and not permis_expire)
        self.db.add(item)
        if permis_expire:
            self.pending_expiry_alerts.append((coop, f"Le permis du chauffeur {user.first_name} {user.name} a expiré le {expiration:%d/%m/%Y}."))
        return item

    def add_vehicle_documents(self, vehicule: Vehicule, *, expired: bool) -> None:
        issued = self.today - timedelta(days=self.rng.randint(200, 330))
        insurance_end = self.today - timedelta(days=20) if expired else issued + timedelta(days=365)
        inspection_end = self.today - timedelta(days=5) if expired else self.today + timedelta(days=self.rng.randint(10, 170))
        self.db.add_all([
            VehiculeDocument(id_vehicule=vehicule.id, type_document="CARTE_GRISE", numero_document=f"CG-{vehicule.immatriculation.replace(' ', '')}",
                             date_delivrance=issued - timedelta(days=700)),
            VehiculeDocument(id_vehicule=vehicule.id, type_document="ASSURANCE", numero_document=f"ASS-{self.rng.randint(100000, 999999)}",
                             date_delivrance=insurance_end - timedelta(days=365), date_expiration=insurance_end),
            VehiculeDocument(id_vehicule=vehicule.id, type_document="VISITE_TECHNIQUE", numero_document=f"VT-{self.rng.randint(10000, 99999)}",
                             date_delivrance=inspection_end - timedelta(days=180), date_expiration=inspection_end, is_valid=not expired),
        ])
        if expired:
            coop = next(c for c in self.cooperatives.values() if c.id == vehicule.id_cooperative)
            self.pending_expiry_alerts.append((coop, f"L'assurance et la visite technique du véhicule {vehicule.immatriculation} ont expiré."))

    # ------------------------------------------------------------------ departures & bookings

    def seed_departures(self) -> None:
        db = self.db
        retarde_done = False
        for offset in range(-PAST_DAYS, FUTURE_DAYS + 1):
            day = self.today + timedelta(days=offset)
            for vehicule, chauffeur, sigle, (a, b), hour in self.operational:
                if self.rng.random() < 0.08:
                    continue  # rest day
                origin, destination = (a, b) if offset % 2 == 0 else (b, a)
                minutes, _ = self.route_info[(origin, destination)]
                dep_at = self.at(day, hour)
                arr_at = dep_at + timedelta(minutes=minutes)
                tarif = self.tarifs.get((sigle, (origin, destination))) or self.tarifs[(None, (origin, destination))]

                statut, started, arrived = self.departure_status(dep_at, arr_at)
                if statut == DepartStatus.EMBARQUEMENT and not retarde_done:
                    statut, retarde_done = DepartStatus.RETARDE, True
                if statut in (DepartStatus.TERMINE, DepartStatus.PROGRAMME) and self.rng.random() < 0.04:
                    statut, started, arrived = DepartStatus.ANNULE, None, None

                depart = Depart(
                    id_itineraire=self.itineraires[(origin, destination)].id, id_cooperative=self.cooperatives[sigle].id,
                    id_vehicule=vehicule.id, id_chauffeur=chauffeur.id, id_tarif=tarif.id,
                    date_depart=day, heure_depart=hour, date_heure_depart=started, date_heure_arrivee=arrived,
                    nombre_places=vehicule.nombre_places, statut=statut,
                    created_at=min(dep_at - timedelta(days=self.rng.randint(5, 14)), self.now),
                )
                db.add(depart)
                db.flush()  # trigger creates the seats

                slug = self.origin_gare_slug(origin, destination)
                ctx = DepartContext(
                    depart=depart, label=f"{origin} → {destination} du {day:%d/%m/%Y} à {hour:%H:%M}",
                    dep_at=dep_at, arr_at=arr_at, gare=self.gares[slug], agent=self.agents[slug], prix=Decimal(tarif.prix),
                )
                self.fill_departure(ctx, offset)
                self.notify_departure(ctx, offset)

    def departure_status(self, dep_at: datetime, arr_at: datetime) -> tuple[str, datetime | None, datetime | None]:
        if arr_at + timedelta(minutes=30) <= self.now:
            started = dep_at + timedelta(minutes=self.rng.randint(0, 25))
            arrived = min(started + (arr_at - dep_at) + timedelta(minutes=self.rng.randint(-20, 45)), self.now)
            return DepartStatus.TERMINE, started, arrived
        if dep_at <= self.now:
            return DepartStatus.PARTI, min(dep_at + timedelta(minutes=self.rng.randint(0, 15)), self.now), None
        if dep_at <= self.now + timedelta(hours=3):
            return DepartStatus.EMBARQUEMENT, None, None
        return DepartStatus.PROGRAMME, None, None

    def fill_departure(self, ctx: DepartContext, offset: int) -> None:
        depart = ctx.depart
        seats = dict(self.db.execute(select(DepartPlace.numero_place, DepartPlace.id).where(DepartPlace.id_depart == depart.id)).all())
        free = sorted(seats)
        if depart.statut != DepartStatus.ANNULE and self.rng.random() < 0.15:
            # Seat 1 is sometimes kept for the convoy agent.
            self.db.execute(update(DepartPlace).where(DepartPlace.id == seats[1]).values(statut=DepartPlaceStatus.BLOQUEE))
            free.remove(1)
        self.rng.shuffle(free)

        if depart.statut == DepartStatus.PROGRAMME:
            fill = max(0.05, 0.7 - 0.09 * offset) * self.rng.uniform(0.7, 1.1)
        elif depart.statut == DepartStatus.ANNULE:
            fill = self.rng.uniform(0.3, 0.6)
        else:
            fill = self.rng.uniform(0.5, 0.95)
        remaining = int(len(free) * fill)

        refusals = 1 if depart.statut in (DepartStatus.EMBARQUEMENT, DepartStatus.RETARDE, DepartStatus.TERMINE) and self.rng.random() < 0.3 else 0
        while remaining > 0 and free:
            size = min(self.rng.choices([1, 2, 3, 4], [50, 30, 12, 8])[0], remaining, len(free))
            chosen = [free.pop() for _ in range(size)]
            remaining -= size
            outcome = self.pick(OUTCOMES[depart.statut])
            refused = refusals > 0 and outcome in ("EMBARQUEE", "TERMINEE")
            refusals -= refused
            self.book(ctx, [seats[n] for n in chosen], outcome, refused=refused)

    def book(self, ctx: DepartContext, place_ids: list[int], outcome: str, *, refused: bool = False) -> None:
        db, rng = self.db, self.rng
        by_passenger = rng.random() < 0.75
        owner = rng.choice(self.active_passengers) if by_passenger else ctx.agent
        if outcome == "EN_ATTENTE" and by_passenger:
            # Respect the per-passenger limit so demo accounts can still book.
            if self.pending_by_user.get(owner.id, 0) >= settings.passenger_max_pending_reservations - 1:
                outcome = "CONFIRMEE"
            else:
                self.pending_by_user[owner.id] = self.pending_by_user.get(owner.id, 0) + 1

        latest = min(ctx.dep_at - timedelta(hours=2), self.now - timedelta(hours=1))
        if outcome == "EN_ATTENTE":
            booked_at = self.now - timedelta(minutes=rng.randint(2, 20))
        else:
            booked_at = self.desk_time(ctx.dep_at - timedelta(days=3), latest)
            if booked_at is None:
                return
        confirmed_at = self.desk_time(booked_at, booked_at + timedelta(minutes=30)) or booked_at
        paid_at = self.desk_time(confirmed_at, confirmed_at + timedelta(minutes=20)) or confirmed_at

        refund_at = None
        if outcome == "REMBOURSEE":
            limit = self.now if ctx.depart.statut == DepartStatus.PROGRAMME else ctx.dep_at - timedelta(minutes=30)
            if ctx.depart.statut == DepartStatus.ANNULE:
                limit = min(self.now, ctx.dep_at + timedelta(days=1))
            refund_at = self.desk_time(paid_at + timedelta(minutes=30), min(limit, self.now))
            if refund_at is None:
                outcome = "ANNULEE"

        reservation = Reservation(
            numero_reservation=f"RES-{uuid4().hex[:22].upper()}",
            id_depart=ctx.depart.id,
            id_user=owner.id,
            montant_total=ctx.prix * len(place_ids),
            statut=ReservationStatus.EN_ATTENTE,
            date_expiration=(self.now if outcome == "EN_ATTENTE" else booked_at) + timedelta(minutes=settings.reservation_hold_minutes),
            created_at=booked_at,
        )
        db.add(reservation)
        db.flush()
        rows = []
        for index, place_id in enumerate(place_ids):
            if index == 0 and by_passenger:
                name, phone = f"{owner.first_name} {owner.name}", owner.telephone
            else:
                first, last = self.person()
                name, phone = f"{first} {last}", self.phone() if rng.random() < 0.7 else None
            rows.append(ReservationPlace(id_reservation=reservation.id, id_depart_place=place_id, nom_passager=name,
                                         telephone_passager=phone, created_at=booked_at))
        db.add_all(rows)
        db.flush()  # trigger marks the seats RESERVEE
        notify = by_passenger
        ctx.bookings.append((reservation.id, owner if notify else None, outcome))

        if outcome == "EN_ATTENTE":
            return
        if outcome == "EXPIREE":
            self.set_reservation_status(reservation, ReservationStatus.EXPIREE, booked_at + timedelta(minutes=settings.reservation_hold_minutes))
            return

        self.set_reservation_status(reservation, ReservationStatus.CONFIRMEE, confirmed_at)
        billets = []
        for row in rows:
            billet = Billet(numero_billet=f"TKT-{uuid4().hex[:30].upper()}", id_reservation_place=row.id, qr_code_uuid=uuid4(),
                            statut=BilletStatus.VALIDE, date_emission=confirmed_at, created_at=confirmed_at)
            filename = f"{billet.numero_billet}.png"
            if self.write_qr:
                qrcode.make(str(billet.qr_code_uuid)).save(self.qr_dir / filename)
            billet.qr_code_path = f"/uploads/qr_codes/{filename}"
            billets.append(billet)
        db.add_all(billets)
        db.flush()
        if notify:
            self.notify(owner, NotificationType.CONFIRMATION_RESERVATION, "Réservation confirmée",
                        f"Votre réservation {reservation.numero_reservation} pour {ctx.label} est confirmée.",
                        confirmed_at, reservation_id=reservation.id, depart_id=ctx.depart.id)

        if outcome == "CONFIRMEE":
            return
        if outcome == "ANNULEE":
            cancelled_at = min(confirmed_at + timedelta(minutes=rng.randint(10, 600)), self.now)
            self.set_reservation_status(reservation, ReservationStatus.ANNULEE, cancelled_at)
            self.set_billets_status(billets, BilletStatus.ANNULE, cancelled_at)
            if notify:
                self.notify(owner, NotificationType.ANNULATION, "Réservation annulée",
                            f"Votre réservation {reservation.numero_reservation} a été annulée.",
                            cancelled_at, reservation_id=reservation.id, depart_id=ctx.depart.id)
            return

        payment = self.pay(ctx, reservation, owner, paid_at, cash_only=not by_passenger)
        if notify:
            self.notify(owner, NotificationType.CONFIRMATION_PAIEMENT, "Paiement reçu",
                        f"Nous avons reçu {payment.montant:,.0f} Ar pour la réservation {reservation.numero_reservation}.".replace(",", " "),
                        paid_at, reservation_id=reservation.id, depart_id=ctx.depart.id)

        if outcome == "PAYEE":
            return
        if outcome == "REMBOURSEE":
            # Trigger cancels the reservation and frees its seats.
            db.execute(update(Paiement).where(Paiement.id == payment.id).values(statut=PaiementStatus.REMBOURSE, updated_at=refund_at))
            caisse = self.caisse(ctx.gare, ctx.agent, refund_at)
            db.add(OperationCaisse(id_caisse=caisse.id, type_operation=OperationType.DEPENSE, montant=payment.montant, id_paiement=payment.id,
                                   description=f"Remboursement {payment.reference_paiement}", date_operation=refund_at, created_at=refund_at))
            self.set_billets_status(billets, BilletStatus.ANNULE, refund_at)
            if notify:
                reason = "suite à l'annulation du départ" if ctx.depart.statut == DepartStatus.ANNULE else "à votre demande"
                self.notify(owner, NotificationType.ANNULATION, "Réservation remboursée",
                            f"Votre réservation {reservation.numero_reservation} a été annulée et remboursée {reason}.",
                            refund_at, reservation_id=reservation.id, depart_id=ctx.depart.id)
            return
        if outcome == "NO_SHOW":
            self.set_billets_status(billets, BilletStatus.EXPIRE, ctx.arr_at)
            return

        if ctx.depart.statut in (DepartStatus.EMBARQUEMENT, DepartStatus.RETARDE):
            boarded_at = max(self.now - timedelta(minutes=rng.randint(1, 20)), paid_at + timedelta(minutes=5))
        else:
            boarded_at = ctx.dep_at - timedelta(minutes=rng.randint(5, 40))
        if refused:
            db.add(Embarquement(id_billet=billets[0].id, id_agent=ctx.agent.id, date_heure_embarquement=boarded_at - timedelta(minutes=3),
                                statut=EmbarquementStatus.REFUSE, motif_refus=rng.choice(REFUSAL_REASONS), created_at=boarded_at - timedelta(minutes=3)))
        for index, billet in enumerate(billets):
            moment = boarded_at + timedelta(seconds=30 * index)
            db.add(Embarquement(id_billet=billet.id, id_agent=ctx.agent.id, date_heure_embarquement=moment,
                                statut=EmbarquementStatus.VALIDE, created_at=moment))
        db.flush()  # trigger: billets UTILISE, seats OCCUPEE, reservation EMBARQUEE
        if notify:
            self.notify(owner, NotificationType.CONFIRMATION_EMBARQUEMENT, "Embarquement validé",
                        f"Bon voyage ! Embarquement validé pour {ctx.label}.",
                        boarded_at, reservation_id=reservation.id, depart_id=ctx.depart.id)
        if outcome == "TERMINEE":
            self.set_reservation_status(reservation, ReservationStatus.TERMINEE, ctx.depart.date_heure_arrivee or ctx.arr_at)

    def pay(self, ctx: DepartContext, reservation: Reservation, owner: User, paid_at: datetime, *, cash_only: bool) -> Paiement:
        db, rng = self.db, self.rng
        methode = PaiementMethode.ESPECES if cash_only else self.pick(
            [(PaiementMethode.ESPECES, 60), (PaiementMethode.MOBILE_MONEY, 35), (PaiementMethode.CARTE, 5)])
        if methode == PaiementMethode.ESPECES:
            reference = f"CASH-{uuid4().hex[:12].upper()}"
        elif methode == PaiementMethode.MOBILE_MONEY:
            reference = f"{rng.choice(['MVOLA', 'ORANGE', 'AIRTEL'])}-{rng.randint(10**9, 10**10 - 1)}"
            if rng.random() < 0.1:
                failed_at = paid_at - timedelta(minutes=3)
                db.add(Paiement(id_reservation=reservation.id, montant=reservation.montant_total, methode=methode,
                                reference_paiement=f"{reference}-KO", statut=PaiementStatus.ECHOUE, date_paiement=failed_at, created_at=failed_at))
        else:
            reference = f"CB-{rng.randint(10**7, 10**8 - 1)}"
        cash = methode == PaiementMethode.ESPECES
        payment = Paiement(id_reservation=reservation.id, montant=reservation.montant_total, methode=methode, reference_paiement=reference,
                           statut=PaiementStatus.VALIDE, date_paiement=paid_at, id_agent=ctx.agent.id if cash else None, created_at=paid_at)
        db.add(payment)
        db.flush()  # trigger marks the reservation PAYEE
        if cash:
            caisse = self.caisse(ctx.gare, ctx.agent, paid_at)
            db.add(OperationCaisse(id_caisse=caisse.id, type_operation=OperationType.RECETTE, montant=payment.montant, id_paiement=payment.id,
                                   id_cooperative=ctx.depart.id_cooperative, description=f"Paiement {reference}",
                                   date_operation=paid_at, created_at=paid_at))
        return payment

    def notify_departure(self, ctx: DepartContext, offset: int) -> None:
        depart = ctx.depart
        active = {"EN_ATTENTE", "CONFIRMEE", "PAYEE", "EMBARQUEE"}
        recipients = [(rid, owner) for rid, owner, outcome in ctx.bookings if owner is not None]
        if depart.statut == DepartStatus.ANNULE:
            sent_at = min(ctx.dep_at - timedelta(hours=6), self.now)
            for rid, owner in recipients:
                self.notify(owner, NotificationType.ANNULATION, "Départ annulé",
                            f"Le départ {ctx.label} est annulé. Votre réservation sera remboursée.", sent_at, reservation_id=rid, depart_id=depart.id)
        elif depart.statut == DepartStatus.RETARDE:
            for rid, owner, outcome in ctx.bookings:
                if owner is not None and outcome in active:
                    self.notify(owner, NotificationType.RETARD, "Départ retardé",
                                f"Le départ {ctx.label} est retardé d'environ 45 minutes.", self.now - timedelta(minutes=10),
                                reservation_id=rid, depart_id=depart.id)
        elif offset == 1:
            for rid, owner, outcome in ctx.bookings:
                if owner is not None and outcome in {"CONFIRMEE", "PAYEE"}:
                    self.notify(owner, NotificationType.RAPPEL_DEPART, "Rappel de départ",
                                f"Votre départ {ctx.label} a lieu demain. Présentez-vous 30 minutes avant.",
                                self.now - timedelta(minutes=self.rng.randint(10, 120)), reservation_id=rid, depart_id=depart.id)
        elif offset >= 3 and self.rng.random() < 0.1:
            for rid, owner, outcome in ctx.bookings:
                if owner is not None and outcome in active:
                    self.notify(owner, NotificationType.MODIFICATION_HORAIRE, "Changement d'horaire",
                                f"Le départ {ctx.label} partira du quai {self.rng.randint(1, 3)}. Merci de vérifier l'horaire.",
                                self.now - timedelta(hours=self.rng.randint(1, 30)), reservation_id=rid, depart_id=depart.id)

    # ------------------------------------------------------------------ cash desks & misc

    def close_cash_desks(self) -> None:
        db = self.db
        for slug, gare in self.gares.items():
            self.caisse(gare, self.agents[slug], self.now)  # every station has an open desk today
        db.flush()

        totals = {
            (caisse_id, type_operation, cooperative_id): Decimal(amount)
            for caisse_id, type_operation, cooperative_id, amount in db.execute(
                select(OperationCaisse.id_caisse, OperationCaisse.type_operation, OperationCaisse.id_cooperative, func.sum(OperationCaisse.montant))
                .group_by(OperationCaisse.id_caisse, OperationCaisse.type_operation, OperationCaisse.id_cooperative)
            ).all()
        }
        sigles = {coop.id: sigle for sigle, coop in self.cooperatives.items()}
        for (_, day), caisse in self.caisses.items():
            if caisse.statut != CaisseStatus.CLOTUREE:
                continue
            closing = self.at(day, time(18, 45))
            recettes = depenses = commissions = Decimal(0)
            for (caisse_id, type_operation, cooperative_id), amount in totals.items():
                if caisse_id != caisse.id:
                    continue
                if type_operation == OperationType.RECETTE:
                    recettes += amount
                    commission = (amount * Decimal("0.05")).quantize(Decimal("1"))
                    if commission > 0:
                        commissions += commission
                        db.add(OperationCaisse(id_caisse=caisse.id, type_operation=OperationType.COMMISSION, montant=commission,
                                               id_cooperative=cooperative_id, description=f"Commission gare 5 % - {sigles[cooperative_id]}",
                                               date_operation=closing, created_at=closing))
                elif type_operation == OperationType.DEPENSE:
                    depenses += amount
            if self.rng.random() < 0.2:
                expense = Decimal(self.rng.choice([5000, 10000, 15000, 20000]))
                depenses += expense
                moment = self.at(day, time(12, 0))
                db.add(OperationCaisse(id_caisse=caisse.id, type_operation=OperationType.DEPENSE, montant=expense,
                                       description=self.rng.choice(["Nettoyage de la gare", "Achat de carnets de reçus", "Eau et électricité"]),
                                       date_operation=moment, created_at=moment))
            solde = Decimal(caisse.montant_ouverture) + recettes - depenses - commissions
            if solde < 0:
                caisse.montant_ouverture = Decimal(caisse.montant_ouverture) - solde
                solde = Decimal(0)
            caisse.montant_cloture = solde
        db.flush()

    def seed_misc(self) -> None:
        for coop, message in self.pending_expiry_alerts:
            sigle = next(s for s, c in self.cooperatives.items() if c.id == coop.id)
            self.notify(self.coop_responsables[sigle], NotificationType.EXPIRATION_DOCUMENT, "Document expiré", message,
                        self.now - timedelta(days=self.rng.randint(1, 5)))
        self.db.add_all([
            RevokedToken(jti=uuid4().hex, token_type="refresh", expires_at=self.now + timedelta(days=5), revoked_at=self.now - timedelta(days=2)),
            RevokedToken(jti=uuid4().hex, token_type="refresh", expires_at=self.now - timedelta(days=1), revoked_at=self.now - timedelta(days=8)),
            RevokedToken(jti=uuid4().hex, token_type="password_reset", expires_at=self.now - timedelta(days=3), revoked_at=self.now - timedelta(days=3, minutes=-10)),
        ])
        self.db.flush()


# ---------------------------------------------------------------------- entry point

def reset_database(db: Session) -> None:
    """Empty every application table and restart their identity sequences."""
    tables = ", ".join(f'"{table.name}"' for table in Base.metadata.sorted_tables)
    db.execute(text(f"TRUNCATE TABLE {tables} RESTART IDENTITY CASCADE"))
    db.commit()
    qr_dir = settings.uploads_dir / "qr_codes"
    if qr_dir.is_dir():
        for path in qr_dir.glob("TKT-*.png"):
            path.unlink()


def has_business_data(db: Session) -> bool:
    business_tables = [Gare, Cooperative, Destination, Vehicule, Depart, Reservation]
    if any(db.scalar(select(func.count()).select_from(model)) for model in business_tables):
        return True
    return (db.scalar(select(func.count()).select_from(User)) or 0) > 1


def print_summary(db: Session) -> None:
    print("\nLignes par table :")
    for table in Base.metadata.sorted_tables:
        count = db.scalar(select(func.count()).select_from(table))
        print(f"  {table.name:<26} {count:>6}")
    print(f"""
Comptes de démonstration (mot de passe : {DEMO_PASSWORD}) :
  admin                     {settings.default_admin_email} (mot de passe DEFAULT_ADMIN_PASSWORD)
  responsable de gare       responsable.gare1@{EMAIL_DOMAIN}, responsable.gare2@{EMAIL_DOMAIN}
  agent de gare             agent.<gare>@{EMAIL_DOMAIN}  (ex. agent.ampasampito, agent.toamasina)
  responsable coopérative   responsable.<sigle>@{EMAIL_DOMAIN}  (fte, mdt, smr, zav)
  chauffeur                 chauffeur01@{EMAIL_DOMAIN} ... chauffeur14@{EMAIL_DOMAIN}
  passager                  passager01@{EMAIL_DOMAIN} ... passager25@{EMAIL_DOMAIN}""")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.db.seed_dev", description="Remplit la base avec des données de démonstration.")
    parser.add_argument("--reset", action="store_true", help="vide toutes les tables (et les QR codes générés) avant de remplir la base")
    parser.add_argument("--empty", action="store_true", help="avec --reset : ne recrée que les rôles, les permissions et le compte admin")
    parser.add_argument("-y", "--yes", action="store_true", help="ne pas demander de confirmation avant --reset")
    parser.add_argument("--seed", type=int, default=2026, help="graine aléatoire (défaut : 2026)")
    parser.add_argument("--no-qr", action="store_true", help="ne pas écrire les images QR (elles sont générées à la demande par l'API)")
    args = parser.parse_args(argv)

    if args.empty and not args.reset:
        parser.error("--empty s'utilise avec --reset")
    if settings.environment.strip().lower() in {"production", "prod"}:
        print("Refusé : ENVIRONMENT vaut 'production'. Ce script est réservé au développement.", file=sys.stderr)
        return 1

    with SessionLocal() as db:
        if args.reset:
            if not args.yes:
                answer = input(f"Toutes les données de {db.bind.url.render_as_string(hide_password=True)} seront supprimées. Tapez RESET pour continuer : ")
                if answer.strip() != "RESET":
                    print("Annulé.")
                    return 1
            reset_database(db)
            print("Base vidée.")
        elif has_business_data(db):
            print("La base contient déjà des données. Relancez avec --reset pour la vider avant de la remplir.", file=sys.stderr)
            return 1

        seed_default_admin(db)
        if args.empty:
            print("Rôles, permissions et compte admin recréés.")
            print_summary(db)
            return 0

        seeder = DemoSeeder(db, random.Random(args.seed), write_qr=not args.no_qr)
        try:
            seeder.run()
            db.commit()
        except Exception:
            db.rollback()
            print("Échec du remplissage : les données de démonstration ont été annulées.", file=sys.stderr)
            raise
        print("Données de démonstration créées.")
        print_summary(db)
    return 0


if __name__ == "__main__":
    sys.exit(main())
