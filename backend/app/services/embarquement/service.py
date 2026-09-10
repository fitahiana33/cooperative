from datetime import date, datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.models.billet import Billet, BilletStatus
from app.models.depart import Depart, DepartStatus
from app.models.embarquement import Embarquement, EmbarquementStatus
from app.models.place import DepartPlaceStatus
from app.models.reservation import Reservation, ReservationPlace, ReservationStatus
from app.models.user import User
from app.services.billet import BilletService
from app.services.notification import NotificationService


class EmbarquementService:
    def __init__(self, db: Session):
        self.db = db

    def control(self, *, code: str, agent: User, date_heure: datetime | None = None) -> Embarquement:
        moment = date_heure or datetime.now(timezone.utc)
        statement = (
            select(Billet)
            .where(Billet.id == Billet.id)
            .options(selectinload(Billet.reservation_place).selectinload(ReservationPlace.reservation).selectinload(Reservation.depart))
            .join(ReservationPlace).join(Reservation).join(Depart)
        )
        try:
            from uuid import UUID
            token = UUID(code)
            statement = statement.where(Billet.qr_code_uuid == token)
        except ValueError:
            statement = statement.where(Billet.numero_billet == code.strip())
        billet = self.db.scalar(statement.with_for_update())
        if not billet:
            from fastapi import HTTPException
            raise HTTPException(404, "Billet introuvable.")
        motif = self._validate(billet, moment)
        if motif:
            result = Embarquement(id_billet=billet.id, id_agent=agent.id, date_heure_embarquement=moment, statut=EmbarquementStatus.REFUSE, motif_refus=motif)
            self.db.add(result)
            self.db.commit()
            self.db.refresh(result)
            return result
        result = Embarquement(id_billet=billet.id, id_agent=agent.id, date_heure_embarquement=moment, statut=EmbarquementStatus.VALIDE)
        self.db.add(result)
        try:
            self.db.flush()
            NotificationService.add(self.db, user_id=billet.reservation_place.reservation.id_user, type_notification="CONFIRMATION_EMBARQUEMENT", titre="Embarquement confirmé", message=f"L'embarquement du billet {billet.numero_billet} est confirmé.", reservation_id=billet.reservation_place.reservation.id, depart_id=billet.reservation_place.reservation.id_depart)
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            result = Embarquement(id_billet=billet.id, id_agent=agent.id, date_heure_embarquement=moment, statut=EmbarquementStatus.REFUSE, motif_refus="Ce billet a déjà été contrôlé.")
            self.db.add(result)
            self.db.commit()
        self.db.refresh(result)
        return result

    @staticmethod
    def _validate(billet: Billet | None, moment: datetime) -> str | None:
        if not billet:
            return "Billet introuvable."
        place = billet.reservation_place
        reservation = place.reservation if place else None
        depart = reservation.depart if reservation else None
        if billet.statut != BilletStatus.VALIDE:
            return "Ce billet est déjà utilisé, annulé ou expiré."
        if not reservation or reservation.statut in {ReservationStatus.ANNULEE, ReservationStatus.EXPIREE, ReservationStatus.TERMINEE}:
            return "La réservation associée n'est pas valide."
        if not depart or depart.date_depart != moment.date():
            return "La date du billet ne correspond pas à la date du contrôle."
        if depart.statut not in {DepartStatus.PROGRAMME, DepartStatus.EMBARQUEMENT, DepartStatus.RETARDE}:
            return "Ce départ n'autorise plus l'embarquement."
        if not place or not place.depart_place or place.depart_place.statut != DepartPlaceStatus.RESERVEE:
            return "La place associée n'est pas disponible pour cet embarquement."
        return None
