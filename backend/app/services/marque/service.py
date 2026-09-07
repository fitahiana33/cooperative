import logging
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.marque import Marque
from app.models.modele import Modele
from app.core.pagination import paginate

logger = logging.getLogger("cooperative.marque")

class MarqueService:
    def __init__(self, db: Session):
        self.db = db

    def list_marques(self, *, page=1, page_size=20, search=None, sort_by="nom", sort_order="asc"):
        return paginate(self.db, Marque, page=page, page_size=page_size, search=search, search_fields=("nom", "description"), sort_by=sort_by, sort_fields=("nom", "created_at"), sort_order=sort_order)

    def get_marque(self, marque_id: int) -> Marque:
        item = self.db.get(Marque, marque_id)
        if not item:
            raise HTTPException(status_code=404, detail="Marque introuvable.")
        return item

    def create_marque(self, *, nom: str, description: str | None = None) -> Marque:
        clean_name = nom.strip()
        if not clean_name:
            raise HTTPException(status_code=422, detail="Le nom de la marque est obligatoire.")
        existing = self.db.scalar(select(Marque).where(func.lower(Marque.nom) == clean_name.lower()))
        if existing:
            raise HTTPException(status_code=400, detail="Une marque avec ce nom existe déjà.")
        item = Marque(nom=clean_name, description=description.strip() if isinstance(description, str) else description)
        try:
            self.db.add(item)
            self.db.commit()
            self.db.refresh(item)
            return item
        except Exception:
            self.db.rollback()
            logger.exception("Erreur lors de la création de la marque nom=%s", nom)
            raise HTTPException(status_code=500, detail="Erreur lors de la création de la marque.")

    def update_marque(self, marque_id: int, **fields) -> Marque:
        item = self.get_marque(marque_id)
        if "nom" in fields and fields["nom"] is not None and not fields["nom"].strip():
            raise HTTPException(status_code=422, detail="Le nom de la marque est obligatoire.")
        if "nom" in fields and fields["nom"]:
            new_nom = fields["nom"].strip()
            if new_nom != item.nom:
                existing = self.db.scalar(select(Marque).where(func.lower(Marque.nom) == new_nom.lower()))
                if existing:
                    raise HTTPException(status_code=400, detail="Une marque avec ce nom existe déjà.")
                item.nom = new_nom
        if "description" in fields:
            item.description = fields["description"]
        if "is_active" in fields and fields["is_active"] is not None:
            item.is_active = fields["is_active"]
        try:
            self.db.commit()
            self.db.refresh(item)
            return item
        except Exception:
            self.db.rollback()
            raise HTTPException(status_code=500, detail="Erreur lors de la modification de la marque.")

    def toggle_marque(self, marque_id: int) -> Marque:
        item = self.get_marque(marque_id)
        item.is_active = not item.is_active
        self.db.commit()
        self.db.refresh(item)
        return item

    def delete_marque(self, marque_id: int) -> None:
        item = self.get_marque(marque_id)
        try:
            self.db.delete(item)
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(status_code=409, detail="Impossible de supprimer une marque liée à des modèles.")
