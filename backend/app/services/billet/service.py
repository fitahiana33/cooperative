from math import ceil
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.billet import Billet
from app.models.depart import Depart
from app.models.reservation import Reservation, ReservationPlace


class BilletService:
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _options():
        return (
            selectinload(Billet.reservation_place).selectinload(ReservationPlace.reservation).selectinload(Reservation.depart),
            selectinload(Billet.reservation_place).selectinload(ReservationPlace.depart_place),
        )

    @staticmethod
    def _to_dict(item: Billet) -> dict:
        place = item.reservation_place
        reservation = place.reservation if place else None
        depart = reservation.depart if reservation else None
        itinerary = depart.itineraire if depart else None
        tariff = depart.tarif if depart else None
        vehicle = depart.vehicule if depart else None
        cooperative = depart.cooperative if depart else None
        return {
            "id": item.id,
            "numero_billet": item.numero_billet,
            "id_reservation_place": item.id_reservation_place,
            "qr_code_uuid": str(item.qr_code_uuid),
            "qr_code_path": item.qr_code_path,
            "statut": item.statut,
            "date_emission": item.date_emission,
            "date_utilisation": item.date_utilisation,
            "reservation_id": reservation.id if reservation else None,
            "numero_reservation": reservation.numero_reservation if reservation else None,
            "id_user": reservation.id_user if reservation else None,
            "nom_passager": place.nom_passager if place else None,
            "telephone_passager": place.telephone_passager if place else None,
            "numero_place": place.depart_place.numero_place if place and place.depart_place else None,
            "id_depart": depart.id if depart else None,
            "date_depart": depart.date_depart if depart else None,
            "heure_depart": depart.heure_depart if depart else None,
            "statut_depart": depart.statut if depart else None,
            "prix": tariff.prix if tariff else None,
            "devise": tariff.devise if tariff else None,
            "destination_depart": itinerary.destination_depart.nom if itinerary and itinerary.destination_depart else None,
            "destination_arrivee": itinerary.destination_arrivee.nom if itinerary and itinerary.destination_arrivee else None,
            "immatriculation": vehicle.immatriculation if vehicle else None,
            "nom_cooperative": cooperative.nom if cooperative else None,
        }

    def _get(self, billet_id: int, *, owner_id: int | None = None, cooperative_ids: set[int] | None = None) -> Billet:
        statement = select(Billet).where(Billet.id == billet_id).options(*self._options()).join(ReservationPlace).join(Reservation).join(Depart)
        if owner_id is not None:
            statement = statement.where(Reservation.id_user == owner_id)
        if cooperative_ids is not None:
            statement = statement.where(Depart.id_cooperative.in_(cooperative_ids))
        item = self.db.scalar(statement)
        if not item:
            raise HTTPException(404, "Billet introuvable.")
        return item

    def get(self, billet_id: int, **scope) -> dict:
        return self._to_dict(self._get(billet_id, **scope))

    def list(self, *, page: int = 1, page_size: int = 20, search: str | None = None, owner_id: int | None = None, cooperative_ids: set[int] | None = None):
        statement = select(Billet).options(*self._options()).join(ReservationPlace).join(Reservation).join(Depart)
        if owner_id is not None:
            statement = statement.where(Reservation.id_user == owner_id)
        if cooperative_ids is not None:
            statement = statement.where(Depart.id_cooperative.in_(cooperative_ids))
        if search and search.strip():
            term = f"%{search.strip()}%"
            statement = statement.where(or_(Billet.numero_billet.ilike(term), Reservation.numero_reservation.ilike(term)))
        total = self.db.scalar(select(func.count()).select_from(statement.order_by(None).subquery())) or 0
        items = list(self.db.scalars(statement.order_by(Billet.date_emission.desc(), Billet.id.desc()).offset((page - 1) * page_size).limit(page_size)).unique())
        return {"items": [self._to_dict(item) for item in items], "total": total, "page": page, "page_size": page_size, "pages": ceil(total / page_size) if total else 0}

    def find_by_code(self, code: str) -> Billet:
        statement = select(Billet).options(*self._options()).join(ReservationPlace).join(Reservation).join(Depart)
        try:
            token = UUID(code)
            statement = statement.where(Billet.qr_code_uuid == token)
        except ValueError:
            statement = statement.where(Billet.numero_billet == code.strip())
        item = self.db.scalar(statement)
        if not item:
            raise HTTPException(404, "Billet introuvable.")
        return item

