import logging
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.marque import Marque
from app.models.modele import Modele
from app.core.pagination import paginate

logger = logging.getLogger("cooperative.modele")

class ModeleService:
    def __init__(self, db: Session):
        self.db = db

    def list_modeles(self, *, page=1, page_size=20, search=None, sort_by="nom", sort_order="asc", id_marque=None):
        query = select(Modele)
        if id_marque:
            query = query.where(Modele.id_marque == id_marque)
        return paginate(self.db, Modele, statement=query, page=page, page_size=page_size, search=search, search_fields=("nom", "description"), sort_by=sort_by, sort_fields=("nom", "created_at"), sort_order=sort_order)

    def get_modele(self, modele_id: int) -> Modele:
        item = self.db.get(Modele, modele_id)
        if not item:
            raise HTTPException(status_code=404, detail="Modèle introuvable.")
        return item

    def create_modele(self, *, id_marque: int, nom: str, description: str | None = None) -> Modele:
        marque = self.db.get(Marque, id_marque)
        if not marque:
            raise HTTPException(status_code=404, detail="Marque introuvable.")
        if not marque.is_active:
            raise HTTPException(status_code=422, detail="La marque sélectionnée est inactive.")
        existing = self.db.scalar(select(Modele).where(
            Modele.id_marque == id_marque,
            func.lower(Modele.nom) == nom.strip().lower(),
        ))
        if existing:
            raise HTTPException(status_code=400, detail="Un modèle avec ce nom existe déjà pour cette marque.")
        item = Modele(id_marque=id_marque, nom=nom.strip(), description=description)
        try:
            self.db.add(item)
            self.db.commit()
            self.db.refresh(item)
            return item
        except Exception:
            self.db.rollback()
            logger.exception("Erreur lors de la création du modèle nom=%s", nom)
            raise HTTPException(status_code=500, detail="Erreur lors de la création du modèle.")

    def update_modele(self, modele_id: int, **fields) -> Modele:
        item = self.get_modele(modele_id)
        next_brand_id = fields.get("id_marque", item.id_marque)
        next_name = fields.get("nom", item.nom)
        if isinstance(next_name, str):
            next_name = next_name.strip()
        if not next_name:
            raise HTTPException(status_code=422, detail="Le nom du modele est obligatoire.")
        duplicate = self.db.scalar(select(Modele).where(
            Modele.id != modele_id,
            Modele.id_marque == next_brand_id,
            func.lower(Modele.nom) == str(next_name).lower(),
        ))
        if duplicate:
            raise HTTPException(status_code=400, detail="Un modele avec ce nom existe deja pour cette marque.")
        if "id_marque" in fields and fields["id_marque"]:
            marque = self.db.get(Marque, fields["id_marque"])
            if not marque:
                raise HTTPException(status_code=404, detail="Marque introuvable.")
            if not marque.is_active:
                raise HTTPException(status_code=422, detail="La marque sélectionnée est inactive.")
            item.id_marque = fields["id_marque"]
        if "nom" in fields and fields["nom"]:
            item.nom = next_name
        if "description" in fields:
            item.description = fields["description"]
        if "is_active" in fields and fields["is_active"] is not None:
            item.is_active = fields["is_active"]
        try:
            self.db.commit()
            self.db.refresh(item)
            return item
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(status_code=400, detail="Informations invalides ou nom déjà existant pour cette marque.")
        except Exception:
            self.db.rollback()
            raise HTTPException(status_code=500, detail="Erreur lors de la modification du modèle.")

    def toggle_modele(self, modele_id: int) -> Modele:
        item = self.get_modele(modele_id)
        item.is_active = not item.is_active
        self.db.commit()
        self.db.refresh(item)
        return item

    def delete_modele(self, modele_id: int) -> None:
        item = self.get_modele(modele_id)
        try:
            self.db.delete(item)
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(status_code=409, detail="Impossible de supprimer un modèle lié à des véhicules.")
