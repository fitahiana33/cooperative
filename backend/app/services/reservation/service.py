from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from math import ceil
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, selectinload

from app.models.billet import Billet, BilletStatus
from app.models.depart import Depart, DepartStatus
from app.models.place import DepartPlace, DepartPlaceStatus
from app.models.reservation import Reservation, ReservationPlace, ReservationStatus
from app.models.tarif import Tarif
from app.models.user import User
from app.services.notification import NotificationService


class ReservationService:
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _options():
        return (
            selectinload(Reservation.depart),
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
        self._expire_if_needed(item)
        return item

    def _expire_if_needed(self, item: Reservation) -> None:
        now = datetime.now(timezone.utc)
        if item.statut == ReservationStatus.EN_ATTENTE and item.date_expiration and item.date_expiration <= now:
            item.statut = ReservationStatus.EXPIREE
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
        items = list(self.db.scalars(statement.order_by(Reservation.created_at.desc(), Reservation.id.desc()).offset((page - 1) * page_size).limit(page_size)).unique())
        for item in items:
            self._expire_if_needed(item)
        return {"items": items, "total": total, "page": page, "page_size": page_size, "pages": ceil(total / page_size) if total else 0}

    def list_places(self, depart_id: int, *, include_unavailable: bool = True) -> list[DepartPlace]:
        depart = self.db.get(Depart, depart_id)
        if not depart:
            raise HTTPException(404, "Départ introuvable.")
        statement = select(DepartPlace).where(DepartPlace.id_depart == depart_id).order_by(DepartPlace.numero_place)
        if not include_unavailable:
            statement = statement.where(DepartPlace.statut == DepartPlaceStatus.DISPONIBLE)
        return list(self.db.scalars(statement))

    def _get_open_depart(self, depart_id: int) -> Depart:
        depart = self.db.get(Depart, depart_id)
        if not depart:
            raise HTTPException(404, "Départ introuvable.")
        if depart.date_depart < date.today():
            raise HTTPException(422, "Ce départ est déjà passé.")
        if depart.statut in {DepartStatus.ANNULE, DepartStatus.TERMINE, DepartStatus.PARTI}:
            raise HTTPException(422, "Ce départ n'accepte plus de réservation.")
        return depart

    def create_reservation(self, *, user: User, depart_id: int, places: list[dict], date_expiration: datetime | None = None) -> Reservation:
        depart = self._get_open_depart(depart_id)
        if not places:
            raise HTTPException(422, "Sélectionnez au moins une place.")
        now = datetime.now(timezone.utc)
        expiration = date_expiration or now + timedelta(minutes=15)
        if expiration <= now:
            raise HTTPException(422, "La date d'expiration de la réservation doit être future.")

        place_ids = sorted({int(item["id_depart_place"]) for item in places})
        locked_places = list(self.db.scalars(
            select(DepartPlace).where(DepartPlace.id_depart_place.in_(place_ids)).order_by(DepartPlace.id_depart_place).with_for_update()
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
            if isinstance(exc, IntegrityError):
                raise HTTPException(409, "Une des places sélectionnées a été réservée entre-temps.")
            raise HTTPException(500, "La réservation n'a pas pu être enregistrée.")

    def confirm(self, reservation_id: int, *, owner_id: int | None = None, cooperative_ids: set[int] | None = None) -> Reservation:
        item = self._get(reservation_id, owner_id=owner_id, cooperative_ids=cooperative_ids)
        if item.statut != ReservationStatus.EN_ATTENTE:
            raise HTTPException(409, "Seule une réservation en attente peut être confirmée.")
        if item.date_expiration and item.date_expiration <= datetime.now(timezone.utc):
            item.statut = ReservationStatus.EXPIREE
            self.db.commit()
            raise HTTPException(409, "Le délai de confirmation de cette réservation est dépassé.")
        item.statut = ReservationStatus.CONFIRMEE
        for place in item.places:
            if not place.billet:
                self.db.add(Billet(
                    numero_billet=f"TKT-{uuid4().hex[:30].upper()}",
                    id_reservation_place=place.id,
                    statut=BilletStatus.VALIDE,
                ))
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

    def cancel(self, reservation_id: int, *, owner_id: int | None = None, cooperative_ids: set[int] | None = None) -> Reservation:
        item = self._get(reservation_id, owner_id=owner_id, cooperative_ids=cooperative_ids)
        if item.statut in {ReservationStatus.ANNULEE, ReservationStatus.EXPIREE, ReservationStatus.EMBARQUEE, ReservationStatus.TERMINEE}:
            raise HTTPException(409, "Cette réservation ne peut plus être annulée.")
        item.statut = ReservationStatus.ANNULEE
        for place in item.places:
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

