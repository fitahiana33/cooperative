import logging
from datetime import date
from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.chauffeur import Chauffeur
from app.models.user import User, UserRole
from app.models.role import Role
from app.models.cooperative import Cooperative, CooperativeMember
from app.models.vehicule import Vehicule, VehiculeChauffeur
from app.core.pagination import paginate

logger = logging.getLogger("cooperative.chauffeur")

class ChauffeurService:
    def __init__(self, db: Session):
        self.db = db

    def _synchronize_expired_permits(self) -> None:
        """Make expired permits unavailable and close their active assignments."""
        today = date.today()
        expired = self.db.scalars(
            select(Chauffeur).where(
                Chauffeur.date_expiration_permis < today,
                or_(
                    Chauffeur.disponibilite.is_(True),
                    Chauffeur.vehicules_assignments.any(VehiculeChauffeur.is_active.is_(True)),
                ),
            )
        )
        changed = False
        for chauffeur in expired:
            chauffeur.disponibilite = False
            self._close_driver_assignments(chauffeur.id)
            changed = True
        if changed:
            self.db.commit()

    def _synchronize_scheduled_assignments(self) -> None:
        """Activate due assignments while preserving driver/vehicle uniqueness."""
        today = date.today()
        due_assignments = list(self.db.scalars(select(VehiculeChauffeur).where(
            VehiculeChauffeur.is_active.is_(False),
            VehiculeChauffeur.date_debut <= today,
            # A closed assignment ending today must not be reactivated by
            # the synchronizer. Open assignments remain eligible; an
            # assignment with a finite end date is due only while it still
            # covers a future day.
            or_(VehiculeChauffeur.date_fin.is_(None), VehiculeChauffeur.date_fin > today),
        ).order_by(VehiculeChauffeur.date_debut, VehiculeChauffeur.created_at)))
        changed = False
        for assignment in due_assignments:
            driver_busy = self.db.scalar(select(VehiculeChauffeur).where(
                VehiculeChauffeur.id_chauffeur == assignment.id_chauffeur,
                VehiculeChauffeur.is_active.is_(True),
            ))
            vehicle_busy = self.db.scalar(select(VehiculeChauffeur).where(
                VehiculeChauffeur.id_vehicule == assignment.id_vehicule,
                VehiculeChauffeur.is_active.is_(True),
            ))
            if driver_busy or vehicle_busy:
                continue
            assignment.is_active = True
            changed = True
        if changed:
            self.db.commit()

    def list_assignments(self, chauffeur_id: int) -> list[VehiculeChauffeur]:
        self._synchronize_scheduled_assignments()
        self.get_chauffeur(chauffeur_id)
        return list(self.db.scalars(select(VehiculeChauffeur).where(
            VehiculeChauffeur.id_chauffeur == chauffeur_id,
        ).order_by(VehiculeChauffeur.date_debut.desc())))

    def close_assignment(self, chauffeur_id: int, vehicule_id: int, date_debut: date) -> None:
        item = self.db.get(VehiculeChauffeur, (vehicule_id, chauffeur_id, date_debut))
        if not item:
            raise HTTPException(status_code=404, detail="Affectation introuvable.")
        if not item.is_active:
            raise HTTPException(status_code=409, detail="Cette affectation est déjà clôturée.")
        if date.today() < date_debut:
            raise HTTPException(status_code=422, detail="Une affectation future ne peut pas encore être clôturée.")
        item.is_active = False
        item.date_fin = date.today()
        self.db.commit()

    def _close_driver_assignments(self, chauffeur_id: int) -> None:
        today = date.today()
        assignments = self.db.scalars(select(VehiculeChauffeur).where(
            VehiculeChauffeur.id_chauffeur == chauffeur_id,
            VehiculeChauffeur.is_active.is_(True),
        ))
        for assignment in assignments:
            assignment.is_active = False
            assignment.date_fin = max(today, assignment.date_debut)

    def list_chauffeurs(
        self,
        *,
        page=1,
        page_size=20,
        search=None,
        sort_by="created_at",
        sort_order="desc",
        id_cooperative=None,
        cooperative_ids: set[int] | None = None,
    ):
        self._synchronize_expired_permits()
        self._synchronize_scheduled_assignments()
        query = select(Chauffeur)
        if id_cooperative is not None:
            query = query.where(Chauffeur.id_cooperative == id_cooperative)
        if cooperative_ids is not None:
            query = query.where(Chauffeur.id_cooperative.in_(cooperative_ids))
        return paginate(
            self.db,
            Chauffeur,
            statement=query,
            page=page,
            page_size=page_size,
            search=search,
            search_fields=("numero_permis", "categorie_permis"),
            sort_by=sort_by,
            sort_fields=("numero_permis", "categorie_permis", "date_expiration_permis", "created_at"),
            sort_order=sort_order,
        )

    def get_chauffeur(self, chauffeur_id: int) -> Chauffeur:
        self._synchronize_expired_permits()
        self._synchronize_scheduled_assignments()
        item = self.db.get(Chauffeur, chauffeur_id)
        if not item:
            raise HTTPException(status_code=404, detail="Chauffeur introuvable.")
        return item

    def get_chauffeur_for_user(self, user_id: int) -> Chauffeur:
        self._synchronize_expired_permits()
        self._synchronize_scheduled_assignments()
        item = self.db.scalar(select(Chauffeur).where(Chauffeur.id_user == user_id))
        if not item:
            raise HTTPException(status_code=404, detail="Aucun profil chauffeur n'est associé à cet utilisateur.")
        return item

    def create_chauffeur(self, *, id_user: int, id_cooperative: int, numero_permis: str, categorie_permis: str, date_expiration_permis: date, disponibilite: bool = True) -> Chauffeur:
        user = self.db.get(User, id_user)
        if not user:
            raise HTTPException(status_code=404, detail="Utilisateur introuvable.")
        if not user.is_active:
            raise HTTPException(status_code=422, detail="Un utilisateur inactif ne peut pas devenir chauffeur.")
        if date_expiration_permis < date.today():
            raise HTTPException(status_code=422, detail="La date d'expiration du permis est déjà dépassée.")
        cooperative = self.db.get(Cooperative, id_cooperative)
        if not cooperative:
            raise HTTPException(status_code=404, detail="Coopérative introuvable.")
        if not cooperative.is_active:
            raise HTTPException(status_code=422, detail="La coopérative sélectionnée est inactive.")

        today = date.today()
        active_member = self.db.scalar(select(CooperativeMember).where(
            CooperativeMember.id_cooperative == id_cooperative,
            CooperativeMember.id_user == id_user,
            CooperativeMember.is_active.is_(True),
            or_(
                CooperativeMember.date_adhesion.is_(None),
                CooperativeMember.date_adhesion <= today,
            ),
            or_(
                CooperativeMember.date_fin.is_(None),
                CooperativeMember.date_fin >= today,
            ),
        ))
        has_chauffeur_role = any(
            role.is_active and role.libelle.strip().lower() == UserRole.CHAUFFEUR
            for role in user.roles
        )
        if not active_member and cooperative.responsable_id != id_user and not has_chauffeur_role:
            raise HTTPException(
                status_code=422,
                detail="L'utilisateur doit avoir le role chauffeur ou etre membre actif de cette cooperative.",
            )

        existing_user = self.db.scalar(select(Chauffeur).where(Chauffeur.id_user == id_user))
        if existing_user:
            raise HTTPException(status_code=400, detail="Cet utilisateur est déjà enregistré comme chauffeur.")

        existing_permis = self.db.scalar(select(Chauffeur).where(Chauffeur.numero_permis == numero_permis.strip()))
        if existing_permis:
            raise HTTPException(status_code=400, detail="Ce numéro de permis est déjà enregisté.")

        item = Chauffeur(
            id_user=id_user,
            id_cooperative=id_cooperative,
            numero_permis=numero_permis.strip(),
            categorie_permis=categorie_permis.strip().upper(),
            date_expiration_permis=date_expiration_permis,
            disponibilite=disponibilite,
        )
        try:
            chauffeur_role = self.db.scalar(select(Role).where(func.lower(Role.libelle) == UserRole.CHAUFFEUR))
            if not chauffeur_role or not chauffeur_role.is_active:
                raise HTTPException(status_code=500, detail="Le rôle chauffeur n'est pas configuré.")
            if chauffeur_role not in user.roles:
                user.roles.append(chauffeur_role)
            self.db.add(item)
            self.db.commit()
            self.db.refresh(item)
            return item
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(status_code=400, detail="Informations de chauffeur invalides.")
        except HTTPException:
            self.db.rollback()
            raise
        except Exception:
            self.db.rollback()
            logger.exception("Erreur création chauffeur user_id=%s", id_user)
            raise HTTPException(status_code=500, detail="Une erreur est survenue lors de la création du chauffeur.")

    def update_chauffeur(self, chauffeur_id: int, **fields) -> Chauffeur:
        item = self.get_chauffeur(chauffeur_id)
        if fields.get("id_cooperative") is not None:
            cooperative = self.db.get(Cooperative, fields["id_cooperative"])
            if not cooperative:
                raise HTTPException(status_code=404, detail="Coopérative introuvable.")
            if not cooperative.is_active:
                raise HTTPException(status_code=422, detail="La coopérative sélectionnée est inactive.")
            if cooperative.id != item.id_cooperative and any(
                assignment.is_active for assignment in item.vehicules_assignments
            ):
                raise HTTPException(
                    status_code=409,
                    detail="Le chauffeur ne peut pas changer de coopérative tant qu'il possède une affectation active.",
                )
        if "numero_permis" in fields and fields["numero_permis"]:
            new_permis = fields["numero_permis"].strip()
            if new_permis != item.numero_permis:
                existing = self.db.scalar(select(Chauffeur).where(Chauffeur.numero_permis == new_permis))
                if existing:
                    raise HTTPException(status_code=400, detail="Ce numéro de permis est déjà enregisté.")
                item.numero_permis = new_permis

        if fields.get("date_expiration_permis") is not None:
            new_expiration = fields["date_expiration_permis"]
            if new_expiration < date.today():
                raise HTTPException(status_code=422, detail="La date d'expiration du permis est déjà dépassée.")
            for assignment in item.vehicules_assignments:
                if assignment.is_active and assignment.date_debut > new_expiration:
                    raise HTTPException(
                        status_code=409,
                        detail="L'expiration du permis ne peut pas précéder une affectation active.",
                    )
                if assignment.is_active and assignment.date_fin is not None and assignment.date_fin > new_expiration:
                    raise HTTPException(
                        status_code=409,
                        detail="L'expiration du permis ne peut pas précéder la fin d'une affectation active.",
                    )
        next_expiration = fields.get("date_expiration_permis", item.date_expiration_permis)
        if fields.get("disponibilite") is True and next_expiration < date.today():
            raise HTTPException(
                status_code=422,
                detail="Un chauffeur dont le permis est expiré ne peut pas être rendu disponible.",
            )

        for key, value in fields.items():
            if key != "numero_permis" and value is not None and hasattr(Chauffeur, key):
                setattr(item, key, value.strip() if isinstance(value, str) else value)

        try:
            if fields.get("is_active") is False and item.is_active is False:
                self._close_driver_assignments(item.id)
            self.db.commit()
            self.db.refresh(item)
            return item
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(status_code=400, detail="Les informations fournies sont invalides.")
        except Exception:
            self.db.rollback()
            raise HTTPException(status_code=500, detail="Erreur lors de la mise à jour du chauffeur.")

    def toggle_chauffeur(self, chauffeur_id: int) -> Chauffeur:
        item = self.get_chauffeur(chauffeur_id)
        item.is_active = not item.is_active
        try:
            if not item.is_active:
                self._close_driver_assignments(item.id)
            self.db.commit()
            self.db.refresh(item)
            return item
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(status_code=409, detail="Impossible de modifier l'état du chauffeur.")

    def delete_chauffeur(self, chauffeur_id: int) -> None:
        item = self.get_chauffeur(chauffeur_id)
        try:
            self.db.delete(item)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise HTTPException(status_code=500, detail="Impossible de supprimer ce chauffeur.")

    # --- Affectations Véhicule ↔ Chauffeur ---
    def assign_to_vehicule(self, chauffeur_id: int, vehicule_id: int, date_debut: date, date_fin: date | None = None) -> VehiculeChauffeur:
        self._synchronize_expired_permits()
        self._synchronize_scheduled_assignments()
        chauffeur = self.get_chauffeur(chauffeur_id)
        vehicule = self.db.get(Vehicule, vehicule_id)
        if not vehicule:
            raise HTTPException(status_code=404, detail="Véhicule introuvable.")

        if not chauffeur.is_active or not chauffeur.disponibilite:
            raise HTTPException(status_code=422, detail="Le chauffeur doit être actif et disponible.")
        if not vehicule.is_active or not vehicule.disponibilite:
            raise HTTPException(status_code=422, detail="Le véhicule doit être actif et disponible.")

        if chauffeur.id_cooperative != vehicule.id_cooperative:
            raise HTTPException(status_code=400, detail="Le chauffeur et le vehicule doivent appartenir a la meme cooperative.")
        if date_debut < date.today():
            raise HTTPException(status_code=422, detail="La date de début d'affectation ne peut pas être antérieure à aujourd'hui.")
        if chauffeur.date_expiration_permis < date_debut:
            raise HTTPException(status_code=422, detail="Le permis du chauffeur est expiré. Affectation impossible.")
        if date_fin is not None and date_fin < date_debut:
            raise HTTPException(status_code=422, detail="La date de fin ne peut pas être antérieure à la date de début.")
        if date_fin is not None and date_fin > chauffeur.date_expiration_permis:
            raise HTTPException(status_code=422, detail="L'affectation ne peut pas dépasser l'expiration du permis.")

        active_assignment = self.db.scalar(select(VehiculeChauffeur).where(
            VehiculeChauffeur.id_chauffeur == chauffeur_id,
            VehiculeChauffeur.is_active.is_(True),
        ))
        if active_assignment:
            raise HTTPException(status_code=409, detail="Ce chauffeur est déjà affecté à un véhicule actif.")

        active_vehicle_assignment = self.db.scalar(select(VehiculeChauffeur).where(
            VehiculeChauffeur.id_vehicule == vehicule_id,
            VehiculeChauffeur.is_active.is_(True),
        ))
        if active_vehicle_assignment:
            raise HTTPException(status_code=409, detail="Ce véhicule est déjà affecté à un chauffeur actif.")

        # Reject overlapping scheduled or current periods, not only rows that
        # are currently marked active. This prevents two future assignments
        # from becoming active on the same day.
        def overlaps(existing: VehiculeChauffeur) -> bool:
            existing_end = existing.date_fin
            return (
                (existing_end is None or existing_end >= date_debut)
                and (date_fin is None or existing.date_debut <= date_fin)
            )

        driver_periods = self.db.scalars(select(VehiculeChauffeur).where(
            VehiculeChauffeur.id_chauffeur == chauffeur_id,
        ))
        if any(overlaps(existing) for existing in driver_periods):
            raise HTTPException(status_code=409, detail="Le chauffeur possède déjà une affectation sur cette période.")
        vehicle_periods = self.db.scalars(select(VehiculeChauffeur).where(
            VehiculeChauffeur.id_vehicule == vehicule_id,
        ))
        if any(overlaps(existing) for existing in vehicle_periods):
            raise HTTPException(status_code=409, detail="Le véhicule possède déjà une affectation sur cette période.")

        today = date.today()
        assignment = VehiculeChauffeur(
            id_vehicule=vehicule_id,
            id_chauffeur=chauffeur_id,
            date_debut=date_debut,
            date_fin=date_fin,
            is_active=date_debut <= today and (date_fin is None or date_fin >= today),
        )
        try:
            self.db.add(assignment)
            self.db.commit()
            self.db.refresh(assignment)
            return assignment
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(
                status_code=409,
                detail="Ce chauffeur est déjà affecté à un véhicule actif ou à ce véhicule à cette date.",
            )
