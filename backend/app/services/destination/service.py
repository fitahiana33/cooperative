import logging

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.pagination import paginate
from app.models.destination import Destination

logger = logging.getLogger("cooperative.destination")


class DestinationService:
    def __init__(self, db: Session):
        self.db = db

    def list_destinations(self, **params):
        return paginate(
            self.db, Destination,
            page=params.get("page", 1), page_size=params.get("page_size", 20),
            search=params.get("search"), search_fields=("nom", "region", "description"),
            sort_by=params.get("sort_by", "nom"), sort_fields=("nom", "region", "created_at"),
            sort_order=params.get("sort_order", "asc"),
        )

    def get_destination(self, destination_id: int) -> Destination:
        item = self.db.get(Destination, destination_id)
        if not item:
            raise HTTPException(404, "Destination introuvable.")
        return item

    def create_destination(self, *, nom: str, region: str | None = None, description: str | None = None) -> Destination:
        clean_name = nom.strip()
        if not clean_name:
            raise HTTPException(422, "Le nom de la destination est obligatoire.")
        if self.db.scalar(select(Destination).where(func.lower(Destination.nom) == clean_name.lower())):
            raise HTTPException(409, "Une destination avec ce nom existe déjà.")
        item = Destination(
            nom=clean_name,
            region=region.strip() if isinstance(region, str) else region,
            description=description.strip() if isinstance(description, str) else description,
        )
        try:
            self.db.add(item)
            self.db.commit()
            self.db.refresh(item)
            return item
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(409, "Une destination avec ce nom existe déjà.")
        except Exception:
            self.db.rollback()
            logger.exception("Erreur création destination")
            raise HTTPException(500, "Une erreur est survenue lors de la création de la destination.")

    def update_destination(self, destination_id: int, **fields) -> Destination:
        item = self.get_destination(destination_id)
        if "nom" in fields and fields["nom"] is not None:
            clean_name = fields["nom"].strip()
            if not clean_name:
                raise HTTPException(422, "Le nom de la destination est obligatoire.")
            duplicate = self.db.scalar(select(Destination).where(
                func.lower(Destination.nom) == clean_name.lower(), Destination.id != item.id,
            ))
            if duplicate:
                raise HTTPException(409, "Une destination avec ce nom existe déjà.")
            item.nom = clean_name
        for key in ("region", "description", "is_active"):
            if key in fields:
                value = fields[key]
                setattr(item, key, value.strip() if isinstance(value, str) else value)
        try:
            self.db.commit()
            self.db.refresh(item)
            return item
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(409, "Cette destination ne peut pas être modifiée.")

    def toggle_destination(self, destination_id: int) -> Destination:
        item = self.get_destination(destination_id)
        item.is_active = not item.is_active
        self.db.commit()
        self.db.refresh(item)
        return item

    def delete_destination(self, destination_id: int) -> None:
        item = self.get_destination(destination_id)
        try:
            self.db.delete(item)
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(409, "Impossible de supprimer une destination utilisée par un itinéraire. Désactivez-la plutôt.")
