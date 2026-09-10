from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session, selectinload

from app.models.billet import Billet
from app.models.chauffeur import Chauffeur
from app.models.cooperative import Cooperative
from app.models.depart import Depart, DepartStatus
from app.models.finance import OperationCaisse, OperationType
from app.models.reservation import Reservation, ReservationPlace, ReservationStatus
from app.models.notification import Notification
from app.models.user import User
from app.models.vehicule import Vehicule
from app.services.notification import NotificationService


class DashboardService:
    def __init__(self, db: Session):
        self.db = db

    def _depart_scope(self, statement, cooperative_ids: set[int] | None):
        if cooperative_ids is not None:
            statement = statement.where(Depart.id_cooperative.in_(cooperative_ids))
        return statement

    def summary(self, *, cooperative_ids: set[int] | None = None) -> dict:
        today = date.today()
        departures = self._depart_scope(select(func.count()).select_from(Depart).where(Depart.date_depart == today), cooperative_ids)
        reservation_statement = select(func.count()).select_from(Reservation).join(Depart).where(Depart.date_depart == today, Reservation.statut.not_in([ReservationStatus.ANNULEE, ReservationStatus.EXPIREE]))
        reservation_statement = self._depart_scope(reservation_statement, cooperative_ids)
        places_statement = self._depart_scope(select(func.coalesce(func.sum(Depart.nombre_places - Depart.places_reservees), 0)).where(Depart.date_depart == today), cooperative_ids)
        revenue_statement = select(func.coalesce(func.sum(OperationCaisse.montant), 0)).where(func.date(OperationCaisse.date_operation) == today, OperationCaisse.type_operation == OperationType.RECETTE)
        revenue = self.db.scalar(revenue_statement) or Decimal("0")
        upcoming = self._depart_scope(
            select(Depart).where(Depart.date_depart >= today, Depart.statut.in_([DepartStatus.PROGRAMME, DepartStatus.EMBARQUEMENT, DepartStatus.RETARDE])).options(selectinload(Depart.itineraire)),
            cooperative_ids,
        ).order_by(Depart.date_depart, Depart.heure_depart).limit(8)
        upcoming_items = list(self.db.scalars(upcoming))
        passagers_statement = select(func.count(distinct(Reservation.id_user))).join(Depart).where(Depart.date_depart == today, Reservation.statut.not_in([ReservationStatus.ANNULEE, ReservationStatus.EXPIREE]))
        passagers_statement = self._depart_scope(passagers_statement, cooperative_ids)
        return {
            "date": today,
            "departs_du_jour": self.db.scalar(departures) or 0,
            "reservations_du_jour": self.db.scalar(reservation_statement) or 0,
            "places_disponibles": self.db.scalar(places_statement) or 0,
            "cooperatives_actives": self.db.scalar(select(func.count()).select_from(Cooperative).where(Cooperative.is_active.is_(True))) or 0,
            "vehicules_actifs": self.db.scalar(select(func.count()).select_from(Vehicule).where(Vehicule.is_active.is_(True))) or 0,
            "chauffeurs_actifs": self.db.scalar(select(func.count()).select_from(Chauffeur).where(Chauffeur.is_active.is_(True))) or 0,
            "passagers_du_jour": self.db.scalar(passagers_statement) or 0,
            "recettes_du_jour": revenue,
            "departs_imminents": upcoming_items,
        }

    def statistics(self, *, date_from: date | None = None, date_to: date | None = None, cooperative_ids: set[int] | None = None) -> dict:
        start = date_from or date.today() - timedelta(days=30)
        end = date_to or date.today()
        departures = self._depart_scope(select(Depart.date_depart, func.count().label("total"), func.sum(Depart.places_reservees).label("places_reservees"), func.sum(Depart.nombre_places).label("places_total")).where(Depart.date_depart.between(start, end)).group_by(Depart.date_depart).order_by(Depart.date_depart), cooperative_ids)
        rows = self.db.execute(departures).all()
        reservations = select(Depart.date_depart, func.count(Reservation.id).label("total")).join(Reservation, Reservation.id_depart == Depart.id).where(Depart.date_depart.between(start, end), Reservation.statut.not_in([ReservationStatus.ANNULEE, ReservationStatus.EXPIREE])).group_by(Depart.date_depart).order_by(Depart.date_depart)
        reservations = self._depart_scope(reservations, cooperative_ids)
        reservation_rows = self.db.execute(reservations).all()
        destinations = select(Depart.id_itineraire, func.count(Reservation.id).label("reservations")).join(Reservation, Reservation.id_depart == Depart.id).where(Depart.date_depart.between(start, end), Reservation.statut.not_in([ReservationStatus.ANNULEE, ReservationStatus.EXPIREE])).group_by(Depart.id_itineraire).order_by(func.count(Reservation.id).desc()).limit(10)
        destinations = self._depart_scope(destinations, cooperative_ids)
        return {
            "date_from": start,
            "date_to": end,
            "departs": [{"date": row.date_depart, "total": row.total, "places_reservees": row.places_reservees or 0, "places_total": row.places_total or 0} for row in rows],
            "reservations": [{"date": row.date_depart, "total": row.total} for row in self.db.execute(reservations).all()],
            "destinations": [{"id_itineraire": row.id_itineraire, "reservations": row.reservations} for row in self.db.execute(destinations).all()],
        }

    def generate_reminders(self, *, now: datetime | None = None) -> int:
        moment = now or datetime.now(timezone.utc)
        target_date = moment.date()
        target_limit = target_date + timedelta(days=1)
        rows = self.db.execute(
            select(Reservation, Depart)
            .join(Depart, Depart.id == Reservation.id_depart)
            .where(Depart.date_depart.between(target_date, target_limit), Reservation.statut.in_([ReservationStatus.CONFIRMEE, ReservationStatus.PAYEE]))
        ).all()
        created = 0
        for reservation, depart in rows:
            exists = self.db.scalar(select(func.count()).select_from(Notification).where(Notification.id_user == reservation.id_user, Notification.id_depart == depart.id, Notification.type_notification == "RAPPEL_DEPART", Notification.date_envoi >= moment - timedelta(hours=20)))
            if exists:
                continue
            NotificationService.add(self.db, user_id=reservation.id_user, type_notification="RAPPEL_DEPART", titre="Rappel de départ", message=f"Votre départ est prévu le {depart.date_depart} à {depart.heure_depart}.", reservation_id=reservation.id, depart_id=depart.id)
            created += 1
        self.db.commit()
        return created
