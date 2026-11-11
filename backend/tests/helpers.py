"""Shared helpers for the API tests."""

from datetime import timedelta

from sqlalchemy import select

from app.core.clock import local_today
from app.models import Caisse, CaisseStatus, Depart, DepartPlace, DepartPlaceStatus, DepartStatus, GareCooperative

API = "/api/v1"


def bookable_departure(db, *, min_free: int = 4, days_ahead: int = 2) -> Depart:
    """A scheduled departure in the near future with enough free seats."""
    target = local_today() + timedelta(days=days_ahead)
    for depart in db.scalars(select(Depart).where(Depart.statut == DepartStatus.PROGRAMME, Depart.date_depart == target).order_by(Depart.id)):
        if free_place_ids(db, depart.id, min_free):
            return depart
    raise AssertionError("Aucun départ réservable dans les données de test.")


def free_place_ids(db, depart_id: int, count: int) -> list[int]:
    ids = list(db.scalars(
        select(DepartPlace.id).where(DepartPlace.id_depart == depart_id, DepartPlace.statut == DepartPlaceStatus.DISPONIBLE).order_by(DepartPlace.numero_place)
    ))
    db.rollback()  # do not keep a snapshot between requests
    return ids[:count] if len(ids) >= count else []


def book(client, headers, depart_id: int, place_ids: list[int], **extra):
    return client.post(f"{API}/reservations", headers=headers, json={
        "id_depart": depart_id,
        "places": [{"id_depart_place": place_id, "nom_passager": f"Passager {place_id}"} for place_id in place_ids],
        **extra,
    })


def open_caisse_for(db, depart: Depart) -> Caisse:
    """An open cash desk at a station where the departure's cooperative operates."""
    caisse = db.scalar(
        select(Caisse).join(GareCooperative, GareCooperative.id_gare == Caisse.id_gare)
        .where(Caisse.statut == CaisseStatus.OUVERTE, GareCooperative.id_cooperative == depart.id_cooperative, GareCooperative.is_active.is_(True))
        .where(Caisse.id_gare == depart.id_gare if depart.id_gare is not None else True)
        .order_by(Caisse.id)
    )
    if caisse is None:
        # Another scenario may have closed the seeded desk. Provision the
        # dependency explicitly instead of relying on test execution order.
        from app.core.config import settings
        from app.models import User
        from app.services.finance import FinanceService
        agent = db.scalar(select(User.id).where(User.email == settings.default_admin_email))
        station_id = depart.id_gare or db.scalar(select(GareCooperative.id_gare).where(GareCooperative.id_cooperative == depart.id_cooperative))
        created = FinanceService(db).open_caisse(gare_id=station_id, agent_id=agent, montant_ouverture=500000)
        caisse = db.get(Caisse, created["id"])
    return caisse


def pay(client, headers, reservation: dict, caisse_id: int):
    return client.post(f"{API}/paiements", headers=headers, json={
        "id_reservation": reservation["id"], "id_caisse": caisse_id, "montant": reservation["montant_total"],
    })
