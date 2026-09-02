import logging
import logging
from datetime import date

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.pagination import paginate
from app.models import Cooperative, CooperativeMember, Gare, GareCooperative, User

logger = logging.getLogger("cooperative.cooperative")


class CooperativeService:
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _validate_dates(date_debut: date | None, date_fin: date | None) -> None:
        if date_fin is not None and date_debut is None:
            raise HTTPException(422, "La date de début est obligatoire lorsque la date de fin est renseignée.")
        if date_debut is not None and date_fin is not None and date_fin < date_debut:
            raise HTTPException(422, "La date de fin ne peut pas être antérieure à la date de début.")

    def list_gare_associations(self, cooperative_id: int) -> list[GareCooperative]:
        self.get_cooperative(cooperative_id)
        statement = select(GareCooperative).where(
            GareCooperative.id_cooperative == cooperative_id,
        )
        return list(self.db.scalars(statement))

    def remove_from_gare(self, gare_id: int, cooperative_id: int) -> None:
        statement = select(GareCooperative).where(
            GareCooperative.id_gare == gare_id,
            GareCooperative.id_cooperative == cooperative_id,
        )
        item = self.db.scalar(statement)
        if not item:
            raise HTTPException(404, "Association gare-coopérative introuvable.")
        item.is_active = False
        self.db.commit()

    def list_members(self, cooperative_id: int) -> list[CooperativeMember]:
        self.get_cooperative(cooperative_id)
        statement = select(CooperativeMember).where(
            CooperativeMember.id_cooperative == cooperative_id,
        )
        return list(self.db.scalars(statement))

    def update_member(self, cooperative_id: int, user_id: int, **fields) -> CooperativeMember:
        self.get_cooperative(cooperative_id)
        statement = select(CooperativeMember).where(
            CooperativeMember.id_cooperative == cooperative_id,
            CooperativeMember.id_user == user_id,
        )
        item = self.db.scalar(statement)
        if not item:
            raise HTTPException(404, "Membre introuvable.")

        next_start = fields.get("date_adhesion", item.date_adhesion)
        next_end = fields.get("date_fin", item.date_fin)
        self._validate_dates(next_start, next_end)
        for key, value in fields.items():
            if value is not None and hasattr(CooperativeMember, key):
                setattr(item, key, value.strip() if isinstance(value, str) else value)
        self.db.commit()
        self.db.refresh(item)
        return item

    def remove_member(self, cooperative_id: int, user_id: int) -> None:
        self.update_member(cooperative_id, user_id, is_active=False)

    def list_cooperatives(
        self, *, page=1, page_size=20, search=None, sort_by="nom", sort_order="asc"
    ):
        return paginate(
            self.db,
            Cooperative,
            page=page,
            page_size=page_size,
            search=search,
            search_fields=("nom", "sigle", "ville"),
            sort_by=sort_by,
            sort_fields=("nom", "sigle", "ville", "created_at"),
            sort_order=sort_order,
        )

    def get_cooperative(self, cooperative_id: int) -> Cooperative:
        item = self.db.get(Cooperative, cooperative_id)
        if not item:
            raise HTTPException(404, "Coopérative introuvable.")
        return item

    def create_cooperative(
        self,
        *,
        nom: str,
        adresse: str | None = None,
        telephone: str | None = None,
        email: str | None = None,
        **fields,
    ) -> Cooperative:
        clean_name = nom.strip()
        if not clean_name:
            raise HTTPException(422, "Le nom de la coopérative est obligatoire.")
        if self.db.scalar(select(Cooperative).where(Cooperative.nom == clean_name)):
            raise HTTPException(400, "Une coopérative portant ce nom existe déjà.")
        if fields.get("responsable_id") is not None and not self.db.get(User, fields["responsable_id"]):
            raise HTTPException(404, "Responsable introuvable.")

        values = {
            key: value.strip() if isinstance(value, str) else value
            for key, value in fields.items()
            if hasattr(Cooperative, key)
        }
        item = Cooperative(
            nom=clean_name,
            adresse=adresse.strip() if isinstance(adresse, str) else adresse,
            telephone=telephone.strip() if isinstance(telephone, str) else telephone,
            email=email.strip().lower() if isinstance(email, str) else email,
            **values,
        )
        try:
            self.db.add(item)
            self.db.commit()
            self.db.refresh(item)
            return item
        except IntegrityError:
            self.db.rollback()
            logger.exception("Création coopérative impossible: nom=%s", clean_name)
            raise HTTPException(400, "Les informations de cette coopérative sont invalides.")
        except Exception:
            self.db.rollback()
            logger.exception("Erreur interne création coopérative: nom=%s", clean_name)
            raise HTTPException(500, "Une erreur est survenue lors de la création de la coopérative.")

    def update_cooperative(self, cooperative_id: int, **fields) -> Cooperative:
        item = self.get_cooperative(cooperative_id)
        if fields.get("responsable_id") is not None and not self.db.get(User, fields["responsable_id"]):
            raise HTTPException(404, "Responsable introuvable.")
        if fields.get("nom") is not None and not fields["nom"].strip():
            raise HTTPException(422, "Le nom de la coopérative est obligatoire.")

        for key, value in fields.items():
            if value is not None and hasattr(Cooperative, key):
                if isinstance(value, str):
                    value = value.strip()
                    if key == "email":
                        value = value.lower()
                setattr(item, key, value)
        try:
            self.db.commit()
            self.db.refresh(item)
            return item
        except IntegrityError:
            self.db.rollback()
            logger.exception("Modification coopérative impossible: id=%s", cooperative_id)
            raise HTTPException(400, "Les informations sont invalides.")
        except Exception:
            self.db.rollback()
            logger.exception("Erreur interne modification coopérative: id=%s", cooperative_id)
            raise HTTPException(500, "Une erreur est survenue lors de la modification.")

    def toggle_cooperative(self, cooperative_id: int) -> Cooperative:
        item = self.get_cooperative(cooperative_id)
        item.is_active = not item.is_active
        try:
            self.db.commit()
            self.db.refresh(item)
            return item
        except Exception:
            self.db.rollback()
            logger.exception("Erreur interne statut coopérative: id=%s", cooperative_id)
            raise HTTPException(500, "Impossible de modifier le statut de cette coopérative.")

    def delete_cooperative(self, cooperative_id: int) -> None:
        item = self.get_cooperative(cooperative_id)
        try:
            self.db.delete(item)
            self.db.commit()
        except Exception:
            self.db.rollback()
            logger.exception("Erreur interne suppression coopérative: id=%s", cooperative_id)
            raise HTTPException(500, "Impossible de supprimer cette coopérative.")

    def attach_to_gare(
        self,
        gare_id: int,
        cooperative_id: int,
        date_debut: date | None = None,
        date_fin: date | None = None,
    ) -> GareCooperative:
        if not self.db.get(Gare, gare_id):
            raise HTTPException(404, "Gare introuvable.")
        self.get_cooperative(cooperative_id)
        self._validate_dates(date_debut, date_fin)

        statement = select(GareCooperative).where(
            GareCooperative.id_gare == gare_id,
            GareCooperative.id_cooperative == cooperative_id,
        )
        existing = self.db.scalar(statement)
        if existing:
            existing.date_debut = date_debut
            existing.date_fin = date_fin
            existing.is_active = True
            self.db.commit()
            self.db.refresh(existing)
            return existing

        item = GareCooperative(
            id_gare=gare_id,
            id_cooperative=cooperative_id,
            date_debut=date_debut,
            date_fin=date_fin,
        )
        try:
            self.db.add(item)
            self.db.commit()
            self.db.refresh(item)
            return item
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(400, "Cette coopérative est déjà associée à cette gare.")

    def add_member(
        self,
        cooperative_id: int,
        user_id: int,
        role_cooperative: str = "MEMBRE",
        date_adhesion: date | None = None,
        date_fin: date | None = None,
    ) -> CooperativeMember:
        self.get_cooperative(cooperative_id)
        if not self.db.get(User, user_id):
            raise HTTPException(404, "Utilisateur introuvable.")
        self._validate_dates(date_adhesion, date_fin)

        statement = select(CooperativeMember).where(
            CooperativeMember.id_cooperative == cooperative_id,
            CooperativeMember.id_user == user_id,
        )
        existing = self.db.scalar(statement)
        if existing:
            existing.fonction = role_cooperative.strip()
            existing.date_adhesion = date_adhesion
            existing.date_fin = date_fin
            existing.is_active = True
            self.db.commit()
            self.db.refresh(existing)
            return existing

        item = CooperativeMember(
            id_cooperative=cooperative_id,
            id_user=user_id,
            fonction=role_cooperative.strip(),
            date_adhesion=date_adhesion,
            date_fin=date_fin,
        )
        try:
            self.db.add(item)
            self.db.commit()
            self.db.refresh(item)
            return item
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(400, "Cet utilisateur est déjà membre de cette coopérative.")
