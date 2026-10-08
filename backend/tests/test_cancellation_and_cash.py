"""Cancellation rules, pending refunds, double payment, cash-desk closing, counter sale."""

from datetime import timedelta
from decimal import Decimal

from sqlalchemy import select, update

from app.core.clock import local_now
from app.models import Caisse, CaisseStatus, Depart, DepartPlace, DepartPlaceStatus, DepartStatus, Gare, Paiement, PaiementStatus, User
from tests.helpers import API, book, bookable_departure, free_place_ids, open_caisse_for, pay
from tests.test_reservations import new_passenger

CASHIER = "responsable.gare1@cooperative.com"


def paid_reservation(client, db, login, *, seats: int = 1):
    passenger = new_passenger(client)
    depart = bookable_departure(db, min_free=seats)
    reservation = book(client, passenger, depart.id, free_place_ids(db, depart.id, seats)).json()
    assert pay(client, login(CASHIER), reservation, open_caisse_for(db, depart).id).status_code in (200, 201)
    return passenger, depart, reservation


def test_passenger_cancelling_paid_reservation_leaves_refund_to_cashier(client, db, login):
    passenger, depart, reservation = paid_reservation(client, db, login)
    response = client.post(f"{API}/reservations/{reservation['id']}/cancel", headers=passenger)
    assert response.status_code == 200, response.text
    assert response.json()["statut"] == "ANNULEE"
    payment = db.scalar(select(Paiement).where(Paiement.id_reservation == reservation["id"]))
    assert payment.statut == PaiementStatus.VALIDE and payment.remboursement_demande_le is not None

    pending = client.get(f"{API}/paiements?a_rembourser=true&page_size=100", headers=login(CASHIER)).json()
    assert payment.id in {item["id"] for item in pending["items"]}

    caisse = open_caisse_for(db, depart)
    refunded = client.post(f"{API}/paiements/{payment.id}/rembourser?id_caisse={caisse.id}", headers=login(CASHIER))
    assert refunded.status_code == 200, refunded.text
    assert refunded.json()["statut"] == "REMBOURSE"


def test_passenger_cannot_cancel_paid_reservation_close_to_departure(client, db, login):
    passenger, depart, reservation = paid_reservation(client, db, login)
    soon = local_now() + timedelta(minutes=30)
    db.execute(update(Depart).where(Depart.id == depart.id).values(date_depart=soon.date(), heure_depart=soon.time().replace(microsecond=0)))
    db.commit()
    response = client.post(f"{API}/reservations/{reservation['id']}/cancel", headers=passenger)
    assert response.status_code == 409


def test_unpaid_reservation_can_be_cancelled_until_departure(client, db):
    passenger = new_passenger(client)
    depart = bookable_departure(db)
    reservation = book(client, passenger, depart.id, free_place_ids(db, depart.id, 1)).json()
    soon = local_now() + timedelta(minutes=30)
    db.execute(update(Depart).where(Depart.id == depart.id).values(date_depart=soon.date(), heure_depart=soon.time().replace(microsecond=0)))
    db.commit()
    assert client.post(f"{API}/reservations/{reservation['id']}/cancel", headers=passenger).status_code == 200


def test_reservation_of_departed_trip_cannot_be_cancelled(client, db, login):
    passenger, depart, reservation = paid_reservation(client, db, login)
    db.execute(update(Depart).where(Depart.id == depart.id).values(statut=DepartStatus.PARTI))
    db.commit()
    response = client.post(f"{API}/reservations/{reservation['id']}/cancel", headers=login(CASHIER))
    assert response.status_code == 409


def test_cooperative_manager_cannot_take_refund_from_a_cash_desk(client, db, login):
    """I-B12: without cash rights the refund is left pending, whatever desk is named."""
    _, depart, reservation = paid_reservation(client, db, login)
    manager = login(f"responsable.{depart.cooperative.sigle.lower()}@cooperative.com")
    caisse = open_caisse_for(db, depart)
    response = client.post(f"{API}/reservations/{reservation['id']}/cancel?id_caisse={caisse.id}", headers=manager)
    assert response.status_code == 200, response.text
    db.expire_all()
    payment = db.scalar(select(Paiement).where(Paiement.id_reservation == reservation["id"]))
    assert payment.statut == PaiementStatus.VALIDE and payment.remboursement_demande_le is not None


def test_cashier_cancellation_refunds_immediately(client, db, login):
    _, depart, reservation = paid_reservation(client, db, login)
    caisse = open_caisse_for(db, depart)
    response = client.post(f"{API}/reservations/{reservation['id']}/cancel?id_caisse={caisse.id}", headers=login(CASHIER))
    assert response.status_code == 200
    db.expire_all()
    payment = db.scalar(select(Paiement).where(Paiement.id_reservation == reservation["id"]))
    assert payment.statut == PaiementStatus.REMBOURSE


def test_reservation_cannot_be_paid_twice(client, db, login):
    _, depart, reservation = paid_reservation(client, db, login)
    again = pay(client, login(CASHIER), reservation, open_caisse_for(db, depart).id)
    assert again.status_code in (409, 422)
    assert db.scalar(select(Paiement.id).where(Paiement.id_reservation == reservation["id"], Paiement.statut == PaiementStatus.VALIDE)) is not None


def test_confirm_refused_on_cancelled_departure(client, db, login):
    staff = login(CASHIER)
    depart = bookable_departure(db)
    reservation = book(client, staff, depart.id, free_place_ids(db, depart.id, 1)).json()
    db.execute(update(Depart).where(Depart.id == depart.id).values(statut=DepartStatus.ANNULE))
    db.commit()
    assert client.post(f"{API}/reservations/{reservation['id']}/confirm", headers=staff).status_code == 409


def test_cash_desk_closing_records_discrepancy(client, db, login):
    """I-B25: the counted cash is kept and the difference recorded; only the desk's agent (or a manager) closes it."""
    caisse = db.scalar(select(Caisse).join(Gare, Gare.id == Caisse.id_gare).where(Caisse.statut == CaisseStatus.OUVERTE, Gare.ville == "Antananarivo").limit(1))
    owner = login(db.get(User, caisse.id_agent).email)
    other_agent = login("agent.toamasina@cooperative.com")
    expected = Decimal(str(client.get(f"{API}/caisses/{caisse.id}", headers=owner).json()["solde"]))
    assert client.post(f"{API}/caisses/{caisse.id}/cloturer", headers=other_agent, json={"montant_cloture": str(expected)}).status_code in (403, 404)
    closed = client.post(f"{API}/caisses/{caisse.id}/cloturer", headers=owner, json={"montant_cloture": str(expected - 5000)})
    assert closed.status_code == 200, closed.text
    assert Decimal(str(closed.json()["ecart_cloture"])) == Decimal("-5000")


def test_counter_sale_books_confirms_and_pays_in_one_step(client, db, login):
    cashier = login(CASHIER)
    depart = bookable_departure(db, min_free=2)
    caisse = open_caisse_for(db, depart)
    response = client.post(f"{API}/reservations/guichet", headers=cashier, json={
        "id_depart": depart.id, "id_caisse": caisse.id,
        "places": [{"id_depart_place": place_id, "nom_passager": "Client Guichet"} for place_id in free_place_ids(db, depart.id, 2)],
    })
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["statut"] == "PAYEE" and all(place["billet"] for place in body["places"])


def test_counter_sale_failure_frees_the_seats(client, db, login):
    cashier = login(CASHIER)
    depart = bookable_departure(db)
    seats = free_place_ids(db, depart.id, 1)
    wrong_desk = db.scalar(select(Caisse.id).where(Caisse.statut == CaisseStatus.CLOTUREE).limit(1))
    response = client.post(f"{API}/reservations/guichet", headers=cashier, json={
        "id_depart": depart.id, "id_caisse": wrong_desk, "places": [{"id_depart_place": seats[0], "nom_passager": "Client Guichet"}],
    })
    assert response.status_code >= 400
    db.rollback()
    assert db.get(DepartPlace, seats[0]).statut == DepartPlaceStatus.DISPONIBLE


def test_passenger_cannot_use_counter_sale(client, db):
    passenger = new_passenger(client)
    depart = bookable_departure(db)
    response = client.post(f"{API}/reservations/guichet", headers=passenger, json={
        "id_depart": depart.id, "places": [{"id_depart_place": free_place_ids(db, depart.id, 1)[0], "nom_passager": "X Y"}],
    })
    assert response.status_code == 403
