import logging
from datetime import date

from fastapi import HTTPException
from sqlalchemy import asc, desc, exists, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, aliased, selectinload
from sqlalchemy.orm.attributes import set_committed_value

from app.models.cooperative import Cooperative
from app.models.destination import Destination
from app.models.itineraire import Itineraire, ItineraireCooperative

logger = logging.getLogger("cooperative.itineraire")


class ItineraireService:
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _validate_dates(start: date | None, end: date | None) -> None:
        if end is not None and start is None:
            raise HTTPException(422, "La date de début est obligatoire lorsque la date de fin est renseignée.")
        if start is not None and end is not None and end < start:
            raise HTTPException(422, "La date de fin ne peut pas être antérieure à la date de début.")

    def _hide_unowned_associations(self, items: list[Itineraire], cooperative_ids: set[int] | None) -> list[Itineraire]:
        if cooperative_ids is None:
            return items
        for item in items:
            set_committed_value(
                item,
                "cooperatives",
                [association for association in item.cooperatives if association.id_cooperative in cooperative_ids],
            )
        return items

    def list_itineraires(self, *, page=1, page_size=20, search=None, sort_by="created_at", sort_order="desc", cooperative_ids: set[int] | None = None):
        depart = aliased(Destination)
        arrivee = aliased(Destination)
        statement = (
            select(Itineraire)
            .join(depart, Itineraire.id_destination_depart == depart.id)
            .join(arrivee, Itineraire.id_destination_arrivee == arrivee.id)
            .options(
                selectinload(Itineraire.destination_depart),
                selectinload(Itineraire.destination_arrivee),
                selectinload(Itineraire.cooperatives).selectinload(ItineraireCooperative.cooperative),
            )
        )
        if search and search.strip():
            term = f"%{search.strip()}%"
            statement = statement.where(or_(depart.nom.ilike(term), arrivee.nom.ilike(term), Itineraire.description.ilike(term)))
        sort_column = {
            "created_at": Itineraire.created_at,
            "distance_km": Itineraire.distance_km,
            "duree_estimee_minutes": Itineraire.duree_estimee_minutes,
        }.get(sort_by, Itineraire.created_at)
        statement = statement.order_by((asc if sort_order == "asc" else desc)(sort_column), Itineraire.id)
        total = self.db.scalar(select(func.count()).select_from(statement.order_by(None).subquery())) or 0
        from math import ceil
        items = list(self.db.scalars(statement.offset((page - 1) * page_size).limit(page_size)).unique())
        items = self._hide_unowned_associations(items, cooperative_ids)
        return {"items": items, "total": total, "page": page, "page_size": page_size, "pages": ceil(total / page_size) if total else 0}

    def get_itineraire(self, itineraire_id: int, *, cooperative_ids: set[int] | None = None) -> Itineraire:
        item = self.db.scalar(
            select(Itineraire).where(Itineraire.id == itineraire_id).options(
                selectinload(Itineraire.destination_depart),
                selectinload(Itineraire.destination_arrivee),
                selectinload(Itineraire.cooperatives).selectinload(ItineraireCooperative.cooperative),
            )
        )
        if not item:
            raise HTTPException(404, "Itinéraire introuvable.")
        self._hide_unowned_associations([item], cooperative_ids)
        return item

    def _validate_destinations(self, departure_id: int, arrival_id: int) -> None:
        if departure_id == arrival_id:
            raise HTTPException(422, "Le départ et l'arrivée doivent être différents.")
        destinations = list(self.db.scalars(select(Destination).where(Destination.id.in_([departure_id, arrival_id]))))
        found = {item.id: item for item in destinations}
        if departure_id not in found or arrival_id not in found:
            raise HTTPException(404, "Une destination sélectionnée est introuvable.")
        if not found[departure_id].is_active or not found[arrival_id].is_active:
            raise HTTPException(422, "Les destinations sélectionnées doivent être actives.")

    def create_itineraire(self, *, id_destination_depart: int, id_destination_arrivee: int, **fields) -> Itineraire:
        self._validate_destinations(id_destination_depart, id_destination_arrivee)
        if self.db.scalar(select(Itineraire).where(
            Itineraire.id_destination_depart == id_destination_depart,
            Itineraire.id_destination_arrivee == id_destination_arrivee,
        )):
            raise HTTPException(409, "Cet itinéraire existe déjà.")
        item = Itineraire(
            id_destination_depart=id_destination_depart,
            id_destination_arrivee=id_destination_arrivee,
            **{key: value.strip() if isinstance(value, str) else value for key, value in fields.items() if key in {"distance_km", "duree_estimee_minutes", "description"}},
        )
        try:
            self.db.add(item)
            self.db.commit()
            return self.get_itineraire(item.id)
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(409, "Les informations de l'itinéraire sont invalides.")
        except Exception:
            self.db.rollback()
            logger.exception("Erreur création itinéraire")
            raise HTTPException(500, "Une erreur est survenue lors de la création de l'itinéraire.")

    def update_itineraire(self, itineraire_id: int, **fields) -> Itineraire:
        item = self.get_itineraire(itineraire_id)
        departure_id = fields.get("id_destination_depart", item.id_destination_depart)
        arrival_id = fields.get("id_destination_arrivee", item.id_destination_arrivee)
        self._validate_destinations(departure_id, arrival_id)
        duplicate = self.db.scalar(select(Itineraire).where(
            Itineraire.id_destination_depart == departure_id,
            Itineraire.id_destination_arrivee == arrival_id,
            Itineraire.id != item.id,
        ))
        if duplicate:
            raise HTTPException(409, "Cet itinéraire existe déjà.")
        for key, value in fields.items():
            if hasattr(Itineraire, key):
                setattr(item, key, value.strip() if isinstance(value, str) else value)
        try:
            self.db.commit()
            return self.get_itineraire(item.id)
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(409, "Les informations de l'itinéraire sont invalides.")

    def toggle_itineraire(self, itineraire_id: int) -> Itineraire:
        item = self.get_itineraire(itineraire_id)
        item.is_active = not item.is_active
        self.db.commit()
        return self.get_itineraire(item.id)

    def delete_itineraire(self, itineraire_id: int) -> None:
        item = self.get_itineraire(itineraire_id)
        try:
            self.db.delete(item)
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(409, "Impossible de supprimer cet itinéraire. Désactivez-le plutôt.")

    def list_cooperatives(self, itineraire_id: int, *, cooperative_ids: set[int] | None = None) -> list[ItineraireCooperative]:
        self.get_itineraire(itineraire_id, cooperative_ids=cooperative_ids)
        statement = select(ItineraireCooperative).where(
            ItineraireCooperative.id_itineraire == itineraire_id,
        )
        if cooperative_ids is not None:
            statement = statement.where(ItineraireCooperative.id_cooperative.in_(cooperative_ids))
        return list(self.db.scalars(statement.options(selectinload(ItineraireCooperative.cooperative))))

    def attach_cooperative(self, itineraire_id: int, cooperative_id: int, *, date_debut: date | None = None, date_fin: date | None = None, is_active: bool = True) -> ItineraireCooperative:
        self.get_itineraire(itineraire_id)
        cooperative = self.db.get(Cooperative, cooperative_id)
        if not cooperative:
            raise HTTPException(404, "Coopérative introuvable.")
        if not cooperative.is_active:
            raise HTTPException(422, "La coopérative sélectionnée est inactive.")
        effective_start = date_debut or date.today()
        self._validate_dates(effective_start, date_fin)
        item = self.db.scalar(select(ItineraireCooperative).where(
            ItineraireCooperative.id_itineraire == itineraire_id,
            ItineraireCooperative.id_cooperative == cooperative_id,
        ))
        if item is None:
            item = ItineraireCooperative(
                id_itineraire=itineraire_id, id_cooperative=cooperative_id,
                date_debut=effective_start, date_fin=date_fin, is_active=is_active,
            )
            self.db.add(item)
        else:
            item.date_debut = effective_start
            item.date_fin = date_fin
            item.is_active = is_active
        try:
            self.db.commit()
            self.db.refresh(item)
            return item
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(409, "Cette coopérative est déjà associée à l'itinéraire.")

    def remove_cooperative(self, itineraire_id: int, cooperative_id: int) -> None:
        item = self.db.scalar(select(ItineraireCooperative).where(
            ItineraireCooperative.id_itineraire == itineraire_id,
            ItineraireCooperative.id_cooperative == cooperative_id,
        ))
        if not item:
            raise HTTPException(404, "Association itinéraire-coopérative introuvable.")
        item.is_active = False
        item.date_fin = max(date.today(), item.date_debut)
        self.db.commit()
