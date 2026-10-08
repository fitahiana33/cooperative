from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import logging
from math import ceil
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, selectinload

from app.models.billet import Billet, BilletStatus
from app.models.depart import Depart, DepartStatus
from app.models.itineraire import Itineraire
from app.models.embarquement import Embarquement, EmbarquementStatus
from app.models.finance import Paiement, PaiementStatus
from app.models.place import DepartPlace, DepartPlaceStatus
from app.models.reservation import Reservation, ReservationPlace, ReservationStatus
from app.models.tarif import Tarif
from app.models.user import User
from app.core.config import settings
from app.services.notification import NotificationService
from app.services.billet import BilletService
from app.services.finance import FinanceService
from app.core.clock import local_moment, local_now, local_today


logger = logging.getLogger("cooperative.reservation")


class ReservationService:
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _options():
        return (
            selectinload(Reservation.depart).selectinload(Depart.itineraire).selectinload(Itineraire.destination_depart),
            selectinload(Reservation.depart).selectinload(Depart.itineraire).selectinload(Itineraire.destination_arrivee),
            selectinload(Reservation.depart).selectinload(Depart.cooperative),
            selectinload(Reservation.places).selectinload(ReservationPlace.depart_place),
            selectinload(Reservation.places).selectinload(ReservationPlace.billet),
        )

    def _get(self, reservation_id: int, *, owner_id: int | None = None, cooperative_ids: set[int] | None = None) -> Reservation:
        statement = select(Reservation).where(Reservation.id == reservation_id).options(*self._options())
        if owner_id is not None:
            statement = statement.where(Reservation.id_user == owner_id)
        if cooperative_ids is not None:
            statement = statement.join(Depart, Depart.id == Reservation.id_depart).where(Depart.id_cooperative.in_(cooperative_ids))
        item = self.db.scalar(statement)
        if not item:
            raise HTTPException(404, "Réservation introuvable.")
        return item

    def _expire_if_needed(self, item: Reservation) -> None:
        now = datetime.now(timezone.utc)
        if item.statut == ReservationStatus.EN_ATTENTE and item.date_expiration and item.date_expiration <= now:
            item.statut = ReservationStatus.EXPIREE
            for place in item.places:
                if place.depart_place and place.depart_place.statut == DepartPlaceStatus.RESERVEE:
                    place.depart_place.statut = DepartPlaceStatus.DISPONIBLE
                if place.billet:
                    place.billet.statut = BilletStatus.ANNULE
            self.db.commit()

    def list_reservations(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
        statut: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        owner_id: int | None = None,
        cooperative_ids: set[int] | None = None,
    ):
        statement = select(Reservation).options(*self._options()).join(Depart, Depart.id == Reservation.id_depart)
        if owner_id is not None:
            statement = statement.where(Reservation.id_user == owner_id)
        if cooperative_ids is not None:
            statement = statement.where(Depart.id_cooperative.in_(cooperative_ids))
        if search and search.strip():
            statement = statement.where(Reservation.numero_reservation.ilike(f"%{search.strip()}%"))
        if statut:
            statement = statement.where(Reservation.statut == statut)
        if date_from:
            statement = statement.where(Depart.date_depart >= date_from)
        if date_to:
            statement = statement.where(Depart.date_depart <= date_to)
        total = self.db.scalar(select(func.count()).select_from(statement.order_by(None).subquery())) or 0
        sort_columns = {
            "created_at": Reservation.created_at,
            "date_expiration": Reservation.date_expiration,
            "montant_total": Reservation.montant_total,
            "statut": Reservation.statut,
            "date_depart": Depart.date_depart,
        }
        sort_column = sort_columns.get(sort_by, Reservation.created_at)
        ordering = sort_column.asc() if sort_order == "asc" else sort_column.desc()
        items = list(self.db.scalars(statement.order_by(ordering, Reservation.id.desc()).offset((page - 1) * page_size).limit(page_size)).unique())
        return {"items": items, "total": total, "page": page, "page_size": page_size, "pages": ceil(total / page_size) if total else 0}

    def list_places(self, depart_id: int, *, include_unavailable: bool = True) -> list[DepartPlace]:
        depart = self.db.get(Depart, depart_id)
        if not depart:
            raise HTTPException(404, "Départ introuvable.")
        statement = select(DepartPlace).where(DepartPlace.id_depart == depart_id).order_by(DepartPlace.numero_place)
        if not include_unavailable:
            statement = statement.where(DepartPlace.statut == DepartPlaceStatus.DISPONIBLE)
        return list(self.db.scalars(statement))

    def manifest_rows(self, depart_id: int) -> list[dict]:
        depart = self.db.get(Depart, depart_id)
        if not depart:
            raise HTTPException(404, "Départ introuvable.")
        statement = (
            select(Reservation)
            .where(
                Reservation.id_depart == depart_id,
                Reservation.statut.notin_([ReservationStatus.ANNULEE, ReservationStatus.EXPIREE]),
            )
            .options(*self._options())
            .order_by(Reservation.id)
        )
        rows: list[dict] = []
        for reservation in self.db.scalars(statement).unique():
            for reservation_place in sorted(reservation.places, key=lambda item: item.depart_place.numero_place if item.depart_place else 0):
                billet = reservation_place.billet
                boarding = None
                if billet:
                    # The valid boarding, if any: a later refused re-scan must not hide it.
                    boarding = self.db.scalar(
                        select(Embarquement)
                        .where(Embarquement.id_billet == billet.id)
                        .order_by((Embarquement.statut == EmbarquementStatus.VALIDE).desc(), Embarquement.date_heure_embarquement.desc(), Embarquement.id.desc())
                    )
                rows.append({
                    "reservation": reservation.numero_reservation,
                    "passager": reservation_place.nom_passager,
                    "telephone": reservation_place.telephone_passager or "",
                    "place": reservation_place.depart_place.numero_place if reservation_place.depart_place else "",
                    "billet": billet.numero_billet if billet else "",
                    "reservation_statut": reservation.statut,
                    "billet_statut": billet.statut if billet else "",
                    "pointage": boarding.statut if boarding else "NON_POINTÉ",
                    "date_pointage": boarding.date_heure_embarquement.isoformat() if boarding else "",
                    "embarque": bool(billet and billet.statut == BilletStatus.UTILISE),
                })
        return rows

    def _get_open_depart(self, depart_id: int) -> Depart:
        depart = self.db.get(Depart, depart_id)
        if not depart:
            raise HTTPException(404, "Départ introuvable.")
        if depart.date_depart < local_today():
            raise HTTPException(422, "Ce départ est déjà passé.")
        if depart.statut in {DepartStatus.ANNULE, DepartStatus.TERMINE, DepartStatus.PARTI}:
            raise HTTPException(422, "Ce départ n'accepte plus de réservation.")
        # A delayed or boarding departure may still take passengers after its
        # scheduled time; a merely scheduled one may not.
        if depart.statut == DepartStatus.PROGRAMME and local_moment(depart.date_depart, depart.heure_depart) <= local_now():
            raise HTTPException(422, "L'heure de ce départ est passée.")
        return depart

    def _sync_depart_place_status(self, place_id: int, statut: DepartPlaceStatus) -> None:
        place = self.db.get(DepartPlace, place_id)
        if place is None:
            return
        place.statut = statut

    def create_reservation(self, *, user: User, depart_id: int, places: list[dict], as_passenger: bool = False) -> Reservation:
        depart = self._get_open_depart(depart_id)
        if not places:
            raise HTTPException(422, "Sélectionnez au moins une place.")
        now = datetime.now(timezone.utc)
        if as_passenger:
            self._check_passenger_limits(user.id, len(places), now)
        # The hold period is decided by the server, never by the client.
        expiration = now + timedelta(minutes=settings.reservation_hold_minutes)

        place_ids = sorted({int(item["id_depart_place"]) for item in places})
        locked_places = list(self.db.scalars(
            select(DepartPlace).where(DepartPlace.id.in_(place_ids)).order_by(DepartPlace.id).with_for_update()
        ))
        if len(locked_places) != len(place_ids) or any(place.id_depart != depart_id for place in locked_places):
            raise HTTPException(422, "Une place sélectionnée ne correspond pas à ce départ.")
        if any(place.statut != DepartPlaceStatus.DISPONIBLE for place in locked_places):
            raise HTTPException(409, "Une des places sélectionnées n'est plus disponible.")

        tarif = self.db.get(Tarif, depart.id_tarif)
        if not tarif:
            raise HTTPException(500, "Le tarif du départ est introuvable.")
        reservation = Reservation(
            numero_reservation=f"RES-{uuid4().hex[:22].upper()}",
            id_depart=depart_id,
            id_user=user.id,
            montant_total=Decimal(tarif.prix) * len(places),
            statut=ReservationStatus.EN_ATTENTE,
            date_expiration=expiration,
        )
        self.db.add(reservation)
        try:
            self.db.flush()
            by_id = {item["id_depart_place"]: item for item in places}
            for place in locked_places:
                data = by_id[place.id]
                self.db.add(ReservationPlace(
                    id_reservation=reservation.id,
                    id_depart_place=place.id,
                    nom_passager=data["nom_passager"],
                    telephone_passager=data.get("telephone_passager"),
                ))
            self.db.commit()
            return self._get(reservation.id)
        except (IntegrityError, SQLAlchemyError) as exc:
            self.db.rollback()
            logger.exception("Erreur création réservation", exc_info=exc)
            if isinstance(exc, IntegrityError):
                raise HTTPException(409, "Une des places sélectionnées a été réservée entre-temps.")
            raise HTTPException(500, "La réservation n'a pas pu être enregistrée.")

    def _check_passenger_limits(self, user_id: int, seat_count: int, now: datetime) -> None:
        if seat_count > settings.passenger_max_seats_per_reservation:
            raise HTTPException(422, f"Vous pouvez réserver au maximum {settings.passenger_max_seats_per_reservation} places à la fois.")
        pending = self.db.scalar(
            select(func.count()).select_from(Reservation).where(
                Reservation.id_user == user_id,
                Reservation.statut == ReservationStatus.EN_ATTENTE,
                Reservation.date_expiration > now,
            )
        ) or 0
        if pending >= settings.passenger_max_pending_reservations:
            raise HTTPException(409, "Vous avez déjà des réservations en attente de paiement. Payez-les ou attendez leur expiration avant d'en créer une autre.")

    def confirm(self, reservation_id: int, *, owner_id: int | None = None, cooperative_ids: set[int] | None = None) -> Reservation:
        item = self._get(reservation_id, owner_id=owner_id, cooperative_ids=cooperative_ids)
        if item.statut != ReservationStatus.EN_ATTENTE:
            raise HTTPException(409, "Seule une réservation en attente peut être confirmée.")
        try:
            self._get_open_depart(item.id_depart)
        except HTTPException as exc:
            raise HTTPException(409, exc.detail)
        if item.date_expiration and item.date_expiration <= datetime.now(timezone.utc):
            item.statut = ReservationStatus.EXPIREE
            self.db.commit()
            raise HTTPException(409, "Le délai de confirmation de cette réservation est dépassé.")
        item.statut = ReservationStatus.CONFIRMEE
        BilletService.issue_for_reservation(self.db, item)
        NotificationService.add(
            self.db,
            user_id=item.id_user,
            type_notification="CONFIRMATION_RESERVATION",
            titre="Réservation confirmée",
            message=f"Votre réservation {item.numero_reservation} est confirmée.",
            reservation_id=item.id,
            depart_id=item.id_depart,
        )
        self.db.commit()
        return self._get(item.id, owner_id=owner_id, cooperative_ids=cooperative_ids)

    def cancel(self, reservation_id: int, *, owner_id: int | None = None, cooperative_ids: set[int] | None = None, caisse_id: int | None = None, agent_id: int | None = None, gare_ids: set[int] | None = None, can_refund_now: bool = False) -> Reservation:
        """Cancel a reservation and free its seats.

        Paid money is returned from a cash desk at once when the caller may
        handle cash (`can_refund_now`) and named an open desk; otherwise the
        payment is flagged for a cashier to refund.
        """
        item = self._get(reservation_id, owner_id=owner_id, cooperative_ids=cooperative_ids)
        if item.statut in {ReservationStatus.ANNULEE, ReservationStatus.EXPIREE, ReservationStatus.EMBARQUEE, ReservationStatus.TERMINEE}:
            raise HTTPException(409, "Cette réservation ne peut plus être annulée.")
        depart = item.depart
        if depart.statut in {DepartStatus.PARTI, DepartStatus.TERMINE}:
            raise HTTPException(409, "Le départ a déjà eu lieu : la réservation ne peut plus être annulée.")
        payments = list(self.db.scalars(select(Paiement).where(Paiement.id_reservation == item.id, Paiement.statut == PaiementStatus.VALIDE)))
        if payments and owner_id is not None and depart.statut != DepartStatus.ANNULE:
            deadline = local_moment(depart.date_depart, depart.heure_depart) - timedelta(minutes=settings.cancellation_deadline_minutes)
            if local_now() > deadline:
                hours = settings.cancellation_deadline_minutes // 60
                raise HTTPException(409, f"Une réservation payée ne peut plus être annulée moins de {hours} h avant le départ.")
        finance = FinanceService(self.db)
        for payment in payments:
            if can_refund_now and caisse_id:
                finance.refund(payment.id, caisse_id=caisse_id, agent_id=agent_id or item.id_user, gare_ids=gare_ids, commit=False)
            else:
                finance.request_refund(payment)
        item.statut = ReservationStatus.ANNULEE
        for place in item.places:
            if place.depart_place is not None:
                place.depart_place.statut = DepartPlaceStatus.DISPONIBLE
            if place.billet:
                place.billet.statut = BilletStatus.ANNULE
        NotificationService.add(
            self.db,
            user_id=item.id_user,
            type_notification="ANNULATION",
            titre="Réservation annulée",
            message=f"Votre réservation {item.numero_reservation} a été annulée.",
            reservation_id=item.id,
            depart_id=item.id_depart,
        )
        self.db.commit()
        return self._get(item.id, owner_id=owner_id, cooperative_ids=cooperative_ids)

    def update_place_status(self, place_id: int, statut: str) -> DepartPlace:
        item = self.db.get(DepartPlace, place_id)
        if not item:
            raise HTTPException(404, "Place introuvable.")
        if item.statut in {DepartPlaceStatus.RESERVEE, DepartPlaceStatus.OCCUPEE}:
            raise HTTPException(409, "Une place réservée ou occupée ne peut pas être bloquée manuellement.")
        if statut not in {DepartPlaceStatus.DISPONIBLE, DepartPlaceStatus.BLOQUEE}:
            raise HTTPException(422, "Une place peut uniquement être disponible ou bloquée manuellement.")
        item.statut = statut
        self.db.commit()
        self.db.refresh(item)
        return item
