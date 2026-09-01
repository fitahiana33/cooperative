import logging
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.models import Emplacement, Gare, Quai, Zone
from app.core.pagination import paginate

logger = logging.getLogger("cooperative.gare")

class GareService:
    def __init__(self, db: Session): self.db = db

    def list_gares(self, *, page=1, page_size=20, search=None, sort_by="nom", sort_order="asc"):
        return paginate(self.db, Gare, page=page, page_size=page_size, search=search, search_fields=("nom", "ville", "adresse"), sort_by=sort_by, sort_fields=("nom", "ville", "adresse", "created_at"), sort_order=sort_order)

    def get_gare(self, gare_id: int) -> Gare:
        gare = self.db.get(Gare, gare_id)
        if not gare: raise HTTPException(404, "Gare introuvable.")
        return gare

    def create_gare(self, *, nom: str, ville: str, adresse: str, latitude: float | None = None, longitude: float | None = None, **fields) -> Gare:
        if self.db.scalar(select(Gare).where(Gare.nom == nom.strip())): raise HTTPException(400, "Une gare portant ce nom existe déjà.")
        gare = Gare(nom=nom.strip(), ville=ville.strip(), adresse=adresse.strip(), latitude=latitude, longitude=longitude, **{k: v for k, v in fields.items() if hasattr(Gare, k)})
        try:
            self.db.add(gare); self.db.commit(); self.db.refresh(gare); return gare
        except IntegrityError:
            self.db.rollback(); logger.exception("Création gare impossible: nom=%s", nom); raise HTTPException(400, "Les informations de cette gare sont invalides.")
        except Exception:
            self.db.rollback(); logger.exception("Erreur interne création gare: nom=%s", nom); raise HTTPException(500, "Une erreur est survenue lors de la création de la gare.")

    def update_gare(self, gare_id: int, **fields) -> Gare:
        gare = self.get_gare(gare_id)
        for key, value in fields.items():
            if value is not None and hasattr(Gare, key): setattr(gare, key, value.strip() if isinstance(value, str) else value)
        try:
            self.db.commit(); self.db.refresh(gare); return gare
        except IntegrityError:
            self.db.rollback(); logger.exception("Modification gare impossible: id=%s", gare_id); raise HTTPException(400, "Les informations de cette gare sont invalides.")
        except Exception:
            self.db.rollback(); logger.exception("Erreur interne modification gare: id=%s", gare_id); raise HTTPException(500, "Une erreur est survenue lors de la modification.")

    def toggle_gare(self, gare_id: int) -> Gare:
        gare = self.get_gare(gare_id); gare.is_active = not gare.is_active
        try: self.db.commit(); self.db.refresh(gare); return gare
        except Exception:
            self.db.rollback(); logger.exception("Erreur interne statut gare: id=%s", gare_id); raise HTTPException(500, "Impossible de modifier le statut de cette gare.")

    def delete_gare(self, gare_id: int) -> None:
        gare = self.get_gare(gare_id)
        try: self.db.delete(gare); self.db.commit()
        except Exception:
            self.db.rollback(); logger.exception("Erreur interne suppression gare: id=%s", gare_id); raise HTTPException(500, "Impossible de supprimer cette gare.")

    def add_quai(self, gare_id: int, *, numero: str, nom: str | None = None, description: str | None = None) -> Quai:
        self.get_gare(gare_id); item = Quai(id_gare=gare_id, numero=numero.strip(), nom=nom, description=description)
        try: self.db.add(item); self.db.commit(); self.db.refresh(item); return item
        except IntegrityError:
            self.db.rollback(); raise HTTPException(400, "Ce numéro de quai existe déjà dans cette gare.")

    def add_zone(self, gare_id: int, *, nom: str, type_zone: str | None = None, description: str | None = None) -> Zone:
        self.get_gare(gare_id); item = Zone(id_gare=gare_id, nom=nom.strip(), type_zone=type_zone, description=description)
        try: self.db.add(item); self.db.commit(); self.db.refresh(item); return item
        except Exception:
            self.db.rollback(); logger.exception("Erreur interne création zone: gare=%s", gare_id); raise HTTPException(500, "Impossible de créer cette zone.")

    def add_emplacement(self, zone_id: int, *, code: str, nom: str | None = None, type_emplacement: str | None = None, description: str | None = None) -> Emplacement:
        if not self.db.get(Zone, zone_id): raise HTTPException(404, "Zone introuvable.")
        item = Emplacement(id_zone=zone_id, code=code.strip(), nom=nom, type_emplacement=type_emplacement, description=description)
        try: self.db.add(item); self.db.commit(); self.db.refresh(item); return item
        except IntegrityError:
            self.db.rollback(); raise HTTPException(400, "Ce code d’emplacement existe déjà dans cette zone.")
