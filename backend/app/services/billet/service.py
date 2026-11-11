from datetime import date
from io import BytesIO
from math import ceil
from uuid import UUID, uuid4

import qrcode

from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.models.billet import Billet, BilletStatus
from app.models.depart import Depart
from app.models.reservation import Reservation, ReservationPlace


class BilletService:
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def issue_for_reservation(db: Session, reservation: Reservation) -> list[Billet]:
        """Create the missing tickets of a reservation, one per reserved seat."""
        created = []
        for place in reservation.places:
            if place.billet is not None:
                continue
            billet = Billet(
                numero_billet=f"TKT-{uuid4().hex[:30].upper()}",
                id_reservation_place=place.id,
                qr_code_uuid=uuid4(),
                statut=BilletStatus.VALIDE,
            )
            # Keep the identity map consistent when confirmation and collection
            # run in the same transaction; a second issuance sees this ticket.
            place.billet = billet
            # QR images are generated on demand by the authenticated endpoint.
            db.add(billet)
            created.append(billet)
        db.flush()
        return created

    @staticmethod
    def qr_png(qr_code_uuid: UUID | str) -> bytes:
        buffer = BytesIO()
        qrcode.make(str(qr_code_uuid)).save(buffer, format="PNG")
        return buffer.getvalue()

    @staticmethod
    def generate_qr(billet: Billet) -> None:
        output_dir = settings.uploads_dir / "qr_codes"
        output_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{billet.numero_billet}.png"
        qrcode.make(str(billet.qr_code_uuid)).save(output_dir / filename)
        billet.qr_code_path = f"/uploads/qr_codes/{filename}"

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

    def _get(self, billet_id: int, *, owner_id: int | None = None, cooperative_ids: set[int] | None = None, chauffeur_id: int | None = None, gare_ids: set[int] | None = None) -> Billet:
        statement = select(Billet).where(Billet.id == billet_id).options(*self._options()).join(ReservationPlace).join(Reservation).join(Depart)
        if owner_id is not None:
            statement = statement.where(Reservation.id_user == owner_id)
        if cooperative_ids is not None:
            statement = statement.where(Depart.id_cooperative.in_(cooperative_ids))
        if gare_ids is not None:
            statement = statement.where(Depart.id_gare.in_(gare_ids))
        if chauffeur_id is not None:
            statement = statement.where(Depart.id_chauffeur == chauffeur_id)
        item = self.db.scalar(statement)
        if not item:
            raise HTTPException(404, "Billet introuvable.")
        return item

    def get(self, billet_id: int, **scope) -> dict:
        return self._to_dict(self._get(billet_id, **scope))

    def list(self, *, page: int = 1, page_size: int = 20, search: str | None = None,
             statut: str | None = None, date_from: date | None = None,
             date_to: date | None = None, id_cooperative: int | None = None,
             id_gare: int | None = None, id_itineraire: int | None = None,
             id_depart: int | None = None, sort_by: str = "date_emission",
             sort_order: str = "desc", owner_id: int | None = None,
             cooperative_ids: set[int] | None = None, chauffeur_id: int | None = None,
             gare_ids: set[int] | None = None):
        statement = select(Billet).options(*self._options()).join(ReservationPlace).join(Reservation).join(Depart)
        if owner_id is not None:
            statement = statement.where(Reservation.id_user == owner_id)
        if cooperative_ids is not None:
            statement = statement.where(Depart.id_cooperative.in_(cooperative_ids))
        if gare_ids is not None:
            statement = statement.where(Depart.id_gare.in_(gare_ids))
        if chauffeur_id is not None:
            statement = statement.where(Depart.id_chauffeur == chauffeur_id)
        if id_cooperative is not None:
            statement = statement.where(Depart.id_cooperative == id_cooperative)
        if id_gare is not None:
            statement = statement.where(Depart.id_gare == id_gare)
        if id_itineraire is not None:
            statement = statement.where(Depart.id_itineraire == id_itineraire)
        if id_depart is not None:
            statement = statement.where(Depart.id == id_depart)
        if date_from is not None:
            statement = statement.where(Depart.date_depart >= date_from)
        if date_to is not None:
            statement = statement.where(Depart.date_depart <= date_to)
        if statut:
            statement = statement.where(Billet.statut == statut)
        if search and search.strip():
            term = f"%{search.strip()}%"
            statement = statement.where(or_(
                Billet.numero_billet.ilike(term),
                Reservation.numero_reservation.ilike(term),
                ReservationPlace.nom_passager.ilike(term),
            ))
        total = self.db.scalar(select(func.count()).select_from(statement.order_by(None).subquery())) or 0
        sort_columns = {
            "date_emission": Billet.date_emission,
            "numero_billet": Billet.numero_billet,
            "numero_reservation": Reservation.numero_reservation,
            "statut": Billet.statut,
        }
        sort_column = sort_columns.get(sort_by, Billet.date_emission)
        order_column = sort_column.asc() if sort_order == "asc" else sort_column.desc()
        items = list(self.db.scalars(statement.order_by(order_column, Billet.id.desc()).offset((page - 1) * page_size).limit(page_size)).unique())
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

