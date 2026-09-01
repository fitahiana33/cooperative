import logging
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.models import Cooperative, CooperativeMember, Gare, GareCooperative, User
from app.core.pagination import paginate

logger = logging.getLogger("cooperative.cooperative")

class CooperativeService:
    def __init__(self, db: Session): self.db = db

    def list_cooperatives(self, *, page=1, page_size=20, search=None, sort_by="nom", sort_order="asc"):
        return paginate(self.db, Cooperative, page=page, page_size=page_size, search=search, search_fields=("nom", "sigle", "ville"), sort_by=sort_by, sort_fields=("nom", "sigle", "ville", "created_at"), sort_order=sort_order)

    def get_cooperative(self, cooperative_id: int) -> Cooperative:
        item = self.db.get(Cooperative, cooperative_id)
        if not item: raise HTTPException(404, "Coopérative introuvable.")
        return item

    def create_cooperative(self, *, nom: str, adresse: str | None = None, telephone: str | None = None, email: str | None = None, **fields) -> Cooperative:
        if self.db.scalar(select(Cooperative).where(Cooperative.nom == nom.strip())): raise HTTPException(400, "Une coopérative portant ce nom existe déjà.")
        item = Cooperative(nom=nom.strip(), adresse=adresse, telephone=telephone, email=email, **{k: v for k, v in fields.items() if hasattr(Cooperative, k)})
        try: self.db.add(item); self.db.commit(); self.db.refresh(item); return item
        except IntegrityError:
            self.db.rollback(); logger.exception("Création coopérative impossible: nom=%s", nom); raise HTTPException(400, "Les informations de cette coopérative sont invalides.")
        except Exception:
            self.db.rollback(); logger.exception("Erreur interne création coopérative: nom=%s", nom); raise HTTPException(500, "Une erreur est survenue lors de la création de la coopérative.")

    def update_cooperative(self, cooperative_id: int, **fields) -> Cooperative:
        item = self.get_cooperative(cooperative_id)
        for key, value in fields.items():
            if value is not None and hasattr(Cooperative, key): setattr(item, key, value.strip() if isinstance(value, str) else value)
        try: self.db.commit(); self.db.refresh(item); return item
        except IntegrityError:
            self.db.rollback(); logger.exception("Modification coopérative impossible: id=%s", cooperative_id); raise HTTPException(400, "Les informations sont invalides.")
        except Exception:
            self.db.rollback(); logger.exception("Erreur interne modification coopérative: id=%s", cooperative_id); raise HTTPException(500, "Une erreur est survenue lors de la modification.")

    def toggle_cooperative(self, cooperative_id: int) -> Cooperative:
        item = self.get_cooperative(cooperative_id); item.is_active = not item.is_active
        try: self.db.commit(); self.db.refresh(item); return item
        except Exception:
            self.db.rollback(); logger.exception("Erreur interne statut coopérative: id=%s", cooperative_id); raise HTTPException(500, "Impossible de modifier le statut de cette coopérative.")

    def delete_cooperative(self, cooperative_id: int) -> None:
        item = self.get_cooperative(cooperative_id)
        try: self.db.delete(item); self.db.commit()
        except Exception:
            self.db.rollback(); logger.exception("Erreur interne suppression coopérative: id=%s", cooperative_id); raise HTTPException(500, "Impossible de supprimer cette coopérative.")

    def attach_to_gare(self, gare_id: int, cooperative_id: int) -> GareCooperative:
        if not self.db.get(Gare, gare_id): raise HTTPException(404, "Gare introuvable.")
        self.get_cooperative(cooperative_id)
        item = GareCooperative(id_gare=gare_id, id_cooperative=cooperative_id)
        try: self.db.add(item); self.db.commit(); self.db.refresh(item); return item
        except IntegrityError:
            self.db.rollback(); raise HTTPException(400, "Cette coopérative est déjà associée à cette gare.")

    def add_member(self, cooperative_id: int, user_id: int, role_cooperative: str = "MEMBRE") -> CooperativeMember:
        self.get_cooperative(cooperative_id)
        if not self.db.get(User, user_id): raise HTTPException(404, "Utilisateur introuvable.")
        item = CooperativeMember(id_cooperative=cooperative_id, id_user=user_id, fonction=role_cooperative)
        try: self.db.add(item); self.db.commit(); self.db.refresh(item); return item
        except IntegrityError:
            self.db.rollback(); raise HTTPException(400, "Cet utilisateur est déjà membre de cette coopérative.")
