import unittest
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from app.models.billet import BilletStatus
from app.models.finance import CaisseStatus, PaiementStatus
from app.models.place import DepartPlaceStatus
from app.models.reservation import ReservationStatus
from app.services.finance.service import FinanceService
from app.services.reservation.service import ReservationService


class FakeSession:
    def __init__(self, objects=None):
        self.objects = objects or {}
        self.added = []
        self.commits = 0

    def get(self, model, identifier):
        direct = self.objects.get((model, identifier))
        if direct is not None:
            return direct
        for item in self.objects.values():
            if getattr(item, "id", None) == identifier:
                return item
        return None

    def add(self, item):
        self.added.append(item)

    def commit(self):
        self.commits += 1

    def refresh(self, _item):
        return None


class BusinessRulesTests(unittest.TestCase):
    def test_expired_reservation_releases_places_and_invalidates_billets(self):
        depart_place = SimpleNamespace(statut=DepartPlaceStatus.RESERVEE)
        billet = SimpleNamespace(statut=BilletStatus.VALIDE)
        reservation = SimpleNamespace(
            statut=ReservationStatus.EN_ATTENTE,
            date_expiration=datetime.now(timezone.utc) - timedelta(minutes=1),
            places=[SimpleNamespace(depart_place=depart_place, billet=billet)],
        )

        ReservationService(FakeSession())._expire_if_needed(reservation)

        self.assertEqual(reservation.statut, ReservationStatus.EXPIREE)
        self.assertEqual(depart_place.statut, DepartPlaceStatus.DISPONIBLE)
        self.assertEqual(billet.statut, BilletStatus.ANNULE)

    def test_refund_cancels_reservation_and_releases_reserved_places(self):
        reservation = SimpleNamespace(
            id=7,
            id_user=11,
            id_depart=3,
            numero_reservation="RES-TEST",
            statut=ReservationStatus.PAYEE,
            places=[SimpleNamespace(
                depart_place=SimpleNamespace(statut=DepartPlaceStatus.RESERVEE),
                billet=SimpleNamespace(statut=BilletStatus.VALIDE),
            )],
        )
        payment = SimpleNamespace(
            id=9,
            id_reservation=reservation.id,
            montant=25000,
            reference_paiement="CASH-TEST",
            statut=PaiementStatus.VALIDE,
            reservation=reservation,
        )
        caisse = SimpleNamespace(id=4, statut=CaisseStatus.OUVERTE)
        session = FakeSession({"payment": payment, "caisse": caisse})

        service = FinanceService(session)
        service.refund(payment.id, caisse_id=4, agent_id=1)

        self.assertEqual(payment.statut, PaiementStatus.REMBOURSE)
        self.assertEqual(reservation.statut, ReservationStatus.ANNULEE)
        self.assertEqual(reservation.places[0].depart_place.statut, DepartPlaceStatus.DISPONIBLE)
        self.assertEqual(reservation.places[0].billet.statut, BilletStatus.ANNULE)
        self.assertGreaterEqual(session.commits, 1)


if __name__ == "__main__":
    unittest.main()