from datetime import date, timedelta
import logging

from fastapi import HTTPException
from sqlalchemy import asc, desc, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.models.cooperative import Cooperative
from app.models.itineraire import Itineraire, ItineraireCooperative
from app.models.tarif import Tarif

logger = logging.getLogger("cooperative.tarif")


class TarifService:
    def __init__(self, db: Session):
        self.db = db

    def _get(self, tarif_id: int) -> Tarif:
        item = self.db.scalar(select(Tarif).where(Tarif.id == tarif_id).options(
            selectinload(Tarif.itineraire), selectinload(Tarif.cooperative),
        ))
        if not item:
            raise HTTPException(404, "Tarif introuvable.")
        return item

    def list_tarifs(self, *, page=1, page_size=20, search=None, sort_by="date_debut", sort_order="desc", id_itineraire=None, cooperative_ids: set[int] | None = None):
        statement = select(Tarif).options(selectinload(Tarif.itineraire), selectinload(Tarif.cooperative))
        if id_itineraire is not None:
            statement = statement.where(Tarif.id_itineraire == id_itineraire)
        if cooperative_ids is not None:
            statement = statement.where((Tarif.id_cooperative.is_(None)) | Tarif.id_cooperative.in_(cooperative_ids))
        if search and search.strip():
            statement = statement.where(Tarif.devise.ilike(f"%{search.strip()}%"))
        sort_column = {
            "date_debut": Tarif.date_debut,
            "prix": Tarif.prix,
            "created_at": Tarif.created_at,
        }.get(sort_by, Tarif.date_debut)
        statement = statement.order_by((asc if sort_order == "asc" else desc)(sort_column), Tarif.id.desc())
        total = self.db.scalar(select(func.count()).select_from(statement.order_by(None).subquery())) or 0
        from math import ceil
        items = list(self.db.scalars(statement.offset((page - 1) * page_size).limit(page_size)))
        return {"items": items, "total": total, "page": page, "page_size": page_size, "pages": ceil(total / page_size) if total else 0}

    def _validate_references(self, itinerary_id: int, cooperative_id: int | None, start: date) -> None:
        itinerary = self.db.get(Itineraire, itinerary_id)
        if not itinerary:
            raise HTTPException(404, "Itinéraire introuvable.")
        if not itinerary.is_active:
            raise HTTPException(422, "L'itinéraire sélectionné est inactif.")
        if cooperative_id is None:
            return
        cooperative = self.db.get(Cooperative, cooperative_id)
        if not cooperative:
            raise HTTPException(404, "Coopérative introuvable.")
        if not cooperative.is_active:
            raise HTTPException(422, "La coopérative sélectionnée est inactive.")
        association = self.db.scalar(select(ItineraireCooperative).where(
            ItineraireCooperative.id_itineraire == itinerary_id,
            ItineraireCooperative.id_cooperative == cooperative_id,
            ItineraireCooperative.is_active.is_(True),
            ItineraireCooperative.date_debut <= start,
            (ItineraireCooperative.date_fin.is_(None) | (ItineraireCooperative.date_fin >= start)),
        ))
        if not association:
            raise HTTPException(422, "La coopérative doit être autorisée sur l'itinéraire à la date du tarif.")

    def _check_active_conflict(self, itinerary_id: int, cooperative_id: int | None, exclude_id: int | None = None) -> None:
        query = select(Tarif).where(Tarif.id_itineraire == itinerary_id, Tarif.is_active.is_(True))
        if cooperative_id is None:
            query = query.where(Tarif.id_cooperative.is_(None))
        else:
            query = query.where(Tarif.id_cooperative == cooperative_id)
        if exclude_id is not None:
            query = query.where(Tarif.id != exclude_id)
        if self.db.scalar(query):
            raise HTTPException(409, "Un tarif actif existe déjà pour cette portée.")

    def create_tarif(self, *, id_itineraire: int, id_cooperative: int | None, prix, devise="MGA", date_debut: date | None = None, date_fin: date | None = None) -> Tarif:
        start = date_debut or date.today()
        if date_fin is not None and date_fin < start:
            raise HTTPException(422, "La date de fin ne peut pas être antérieure à la date de début.")
        self._validate_references(id_itineraire, id_cooperative, start)
        self._check_active_conflict(id_itineraire, id_cooperative)
        item = Tarif(id_itineraire=id_itineraire, id_cooperative=id_cooperative, prix=prix, devise=devise.strip().upper(), date_debut=start, date_fin=date_fin)
        try:
            self.db.add(item)
            self.db.commit()
            return self._get(item.id)
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(409, "Un tarif actif existe déjà pour cette portée.")
        except Exception:
            self.db.rollback()
            logger.exception("Erreur création tarif")
            raise HTTPException(500, "Une erreur est survenue lors de la création du tarif.")

    def update_tarif(self, tarif_id: int, **fields) -> Tarif:
        current = self._get(tarif_id)
        if fields.get("is_active") is False and all(key in {"is_active"} for key in fields):
            return self.toggle_tarif(tarif_id)
        itinerary_id = current.id_itineraire
        cooperative_id = fields.get("id_cooperative", current.id_cooperative)
        start = fields.get("date_debut", current.date_debut) or date.today()
        end = fields.get("date_fin", current.date_fin)
        if end is not None and end < start:
            raise HTTPException(422, "La date de fin ne peut pas être antérieure à la date de début.")
        self._validate_references(itinerary_id, cooperative_id, start)

        # An active tariff is versioned instead of overwritten. The previous
        # row remains available in the history with an end date.
        if current.is_active and any(key != "is_active" for key in fields):
            if start < current.date_debut:
                raise HTTPException(422, "La nouvelle version ne peut pas commencer avant le tarif actuel.")
            self._check_active_conflict(itinerary_id, cooperative_id, exclude_id=current.id)
            current.is_active = False
            current.date_fin = max(current.date_debut, start - timedelta(days=1))
            self.db.flush()
            version = Tarif(
                id_itineraire=itinerary_id,
                id_cooperative=cooperative_id,
                prix=fields.get("prix", current.prix),
                devise=(fields.get("devise", current.devise).strip().upper()
                        if isinstance(fields.get("devise", current.devise), str)
                        else current.devise),
                date_debut=start,
                date_fin=end,
                is_active=fields.get("is_active", True),
            )
            self.db.add(version)
            try:
                self.db.commit()
                return self._get(version.id)
            except IntegrityError:
                self.db.rollback()
                raise HTTPException(409, "Les informations du tarif sont invalides.")

        if fields.get("is_active", True):
            self._check_active_conflict(itinerary_id, cooperative_id, exclude_id=current.id)
        changed = {key: value for key, value in fields.items() if key != "is_active"}
        for key, value in changed.items():
            if hasattr(Tarif, key):
                setattr(current, key, value.strip().upper() if key == "devise" and isinstance(value, str) else value)
        if fields.get("is_active") is not None:
            current.is_active = fields["is_active"]
        try:
            self.db.commit()
            return self._get(current.id)
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(409, "Les informations du tarif sont invalides.")

    def toggle_tarif(self, tarif_id: int) -> Tarif:
        item = self._get(tarif_id)
        if item.is_active:
            item.is_active = False
            item.date_fin = max(date.today(), item.date_debut) if item.date_fin is None else item.date_fin
        else:
            self._validate_references(item.id_itineraire, item.id_cooperative, item.date_debut)
            self._check_active_conflict(item.id_itineraire, item.id_cooperative, exclude_id=item.id)
            item.is_active = True
            if item.date_fin and item.date_fin < date.today():
                item.date_fin = None
        self.db.commit()
        return self._get(item.id)

    def history(self, itinerary_id: int, *, cooperative_ids: set[int] | None = None) -> list[Tarif]:
        statement = select(Tarif).where(Tarif.id_itineraire == itinerary_id).options(selectinload(Tarif.itineraire), selectinload(Tarif.cooperative))
        if cooperative_ids is not None:
            statement = statement.where((Tarif.id_cooperative.is_(None)) | Tarif.id_cooperative.in_(cooperative_ids))
        return list(self.db.scalars(statement.order_by(Tarif.date_debut.desc(), Tarif.id.desc())))
