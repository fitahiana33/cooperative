import logging
from datetime import date

from fastapi import HTTPException
from sqlalchemy import and_, exists, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.roles import normalize_role
from app.core.pagination import paginate
from app.models import Chauffeur, Cooperative, CooperativeMember, Gare, GareCooperative, Role, User
from app.models.user import UserRole

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
        cooperative = self.get_cooperative(cooperative_id)
        if cooperative.responsable_id == user_id:
            raise HTTPException(409, "Le responsable doit être remplacé avant de retirer ce membre.")
        self.update_member(cooperative_id, user_id, is_active=False)

    def list_cooperatives(
        self,
        *,
        page=1,
        page_size=20,
        search=None,
        sort_by="nom",
        sort_order="asc",
        cooperative_ids: set[int] | None = None,
    ):
        statement = select(Cooperative)
        if cooperative_ids is not None:
            statement = statement.where(Cooperative.id.in_(cooperative_ids))
        return paginate(
            self.db,
            Cooperative,
            statement=statement,
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

    def list_eligible_chauffeur_users(self, cooperative_id: int) -> list[User]:
        """Return active users eligible to receive a chauffeur profile."""
        cooperative = self.get_cooperative(cooperative_id)
        if not cooperative.is_active:
            raise HTTPException(422, "La coopérative sélectionnée est inactive.")
        today = date.today()
        member_exists = exists(select(CooperativeMember.id_user).where(
            CooperativeMember.id_cooperative == cooperative_id,
            CooperativeMember.id_user == User.id,
            CooperativeMember.is_active.is_(True),
            or_(CooperativeMember.date_adhesion.is_(None), CooperativeMember.date_adhesion <= today),
            or_(CooperativeMember.date_fin.is_(None), CooperativeMember.date_fin >= today),
        ))
        driver_exists = exists(select(Chauffeur.id).where(Chauffeur.id_user == User.id))
        chauffeur_role_exists = User.roles.any(and_(
            Role.is_active.is_(True),
            func.lower(Role.libelle) == UserRole.CHAUFFEUR,
        ))
        return list(self.db.scalars(
            select(User)
            .where(
                User.is_active.is_(True),
                or_(
                    User.id == cooperative.responsable_id,
                    member_exists,
                    chauffeur_role_exists,
                ),
            )
            .where(~driver_exists)
            .order_by(User.name, User.first_name, User.id)
        ))

    def list_eligible_members(self, cooperative_id: int) -> list[User]:
        """Return active users who can be added to this cooperative."""
        cooperative = self.get_cooperative(cooperative_id)
        if not cooperative.is_active:
            raise HTTPException(422, "La coopÃ©rative sÃ©lectionnÃ©e est inactive.")

        active_member_exists = exists(select(CooperativeMember.id_user).where(
            CooperativeMember.id_cooperative == cooperative_id,
            CooperativeMember.id_user == User.id,
            CooperativeMember.is_active.is_(True),
        ))
        return list(self.db.scalars(
            select(User)
            .where(User.is_active.is_(True), ~active_member_exists)
            .order_by(User.name, User.first_name, User.id)
        ))

    def list_eligible_responsables(self) -> list[User]:
        """Return active users with the canonical cooperative manager role."""
        return list(self.db.scalars(
            select(User)
            .join(User.roles)
            .where(
                User.is_active.is_(True),
                Role.is_active.is_(True),
                func.lower(Role.libelle) == UserRole.RESPONSABLE_COOPERATIVE,
            )
            .distinct()
            .order_by(User.name, User.first_name, User.id)
        ))

    def list_available_gares(self, cooperative_id: int) -> list[Gare]:
        """Return active stations not currently attached to the cooperative."""
        cooperative = self.get_cooperative(cooperative_id)
        if not cooperative.is_active:
            raise HTTPException(422, "La coopÃ©rative sÃ©lectionnÃ©e est inactive.")
        association_exists = exists(select(GareCooperative.id_gare).where(
            GareCooperative.id_gare == Gare.id,
            GareCooperative.id_cooperative == cooperative_id,
            GareCooperative.is_active.is_(True),
        ))
        return list(self.db.scalars(
            select(Gare)
            .where(Gare.is_active.is_(True), ~association_exists)
            .order_by(Gare.nom, Gare.ville, Gare.id)
        ))

    def _validate_responsable(self, user_id: int | None) -> User | None:
        if user_id is None:
            return None
        user = self.db.get(User, user_id)
        if not user:
            raise HTTPException(404, "Responsable introuvable.")
        if not user.is_active:
            raise HTTPException(422, "Un utilisateur inactif ne peut pas être responsable.")
        if not any(
            role.is_active and normalize_role(role.libelle) == UserRole.RESPONSABLE_COOPERATIVE
            for role in user.roles
        ):
            raise HTTPException(
                422,
                "Le responsable doit posséder le rôle responsable_cooperative.",
            )
        return user

    def _ensure_responsable_membership(self, cooperative_id: int, user_id: int) -> None:
        member = self.db.scalar(select(CooperativeMember).where(
            CooperativeMember.id_cooperative == cooperative_id,
            CooperativeMember.id_user == user_id,
        ))
        if member:
            member.is_active = True
            member.fonction = "RESPONSABLE"
            if member.date_adhesion is None:
                member.date_adhesion = date.today()
            return
        self.db.add(CooperativeMember(
            id_cooperative=cooperative_id,
            id_user=user_id,
            fonction="RESPONSABLE",
            date_adhesion=date.today(),
            is_active=True,
        ))

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
        if self.db.scalar(select(Cooperative).where(func.lower(Cooperative.nom) == clean_name.lower())):
            raise HTTPException(400, "Une coopérative portant ce nom existe déjà.")
        responsable_id = fields.get("responsable_id")
        self._validate_responsable(responsable_id)

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
            self.db.flush()
            if responsable_id is not None:
                self._ensure_responsable_membership(item.id, responsable_id)
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
        if "responsable_id" in fields:
            self._validate_responsable(fields["responsable_id"])
        if fields.get("nom") is not None and not fields["nom"].strip():
            raise HTTPException(422, "Le nom de la coopérative est obligatoire.")

        if fields.get("nom") and fields["nom"].strip().lower() != item.nom.lower():
            duplicate = self.db.scalar(select(Cooperative).where(
                Cooperative.id != cooperative_id,
                func.lower(Cooperative.nom) == fields["nom"].strip().lower(),
            ))
            if duplicate:
                raise HTTPException(400, "Une cooperative portant ce nom existe deja.")

        for key, value in fields.items():
            if key == "responsable_id":
                item.responsable_id = value
                if value is not None:
                    self._ensure_responsable_membership(item.id, value)
            elif hasattr(Cooperative, key):
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
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(
                status_code=409,
                detail="Impossible de supprimer une coopérative encore liée à des véhicules ou chauffeurs.",
            )
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
        cooperative = self.get_cooperative(cooperative_id)
        if not cooperative.is_active:
            raise HTTPException(422, "Une coopérative inactive ne peut pas être rattachée à une gare.")
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
        cooperative = self.get_cooperative(cooperative_id)
        if not cooperative.is_active:
            raise HTTPException(422, "Une coopérative inactive ne peut pas recevoir de membre.")
        user = self.db.get(User, user_id)
        if not user:
            raise HTTPException(404, "Utilisateur introuvable.")
        if not user.is_active:
            raise HTTPException(422, "Un utilisateur inactif ne peut pas devenir membre.")
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
