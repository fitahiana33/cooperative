import logging
from datetime import date
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.chauffeur import Chauffeur
from app.models.user import User, UserRole
from app.models.role import Role
from app.models.cooperative import Cooperative
from app.models.vehicule import Vehicule, VehiculeChauffeur
from app.core.pagination import paginate

logger = logging.getLogger("cooperative.chauffeur")

class ChauffeurService:
    def __init__(self, db: Session):
        self.db = db

    def list_assignments(self, chauffeur_id: int) -> list[VehiculeChauffeur]:
        self.get_chauffeur(chauffeur_id)
        return list(self.db.scalars(select(VehiculeChauffeur).where(
            VehiculeChauffeur.id_chauffeur == chauffeur_id,
        ).order_by(VehiculeChauffeur.date_debut.desc())))

    def close_assignment(self, chauffeur_id: int, vehicule_id: int, date_debut: date) -> None:
        item = self.db.get(VehiculeChauffeur, (vehicule_id, chauffeur_id, date_debut))
        if not item:
            raise HTTPException(status_code=404, detail="Affectation introuvable.")
        if date.today() < date_debut:
            raise HTTPException(status_code=422, detail="Une affectation future ne peut pas encore être clôturée.")
        item.is_active = False
        item.date_fin = date.today()
        self.db.commit()

    def list_chauffeurs(self, *, page=1, page_size=20, search=None, sort_by="created_at", sort_order="desc", id_cooperative=None):
        query = select(Chauffeur)
        if id_cooperative:
            query = query.where(Chauffeur.id_cooperative == id_cooperative)
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
        item = self.db.get(Chauffeur, chauffeur_id)
        if not item:
            raise HTTPException(status_code=404, detail="Chauffeur introuvable.")
        return item

    def create_chauffeur(self, *, id_user: int, id_cooperative: int, numero_permis: str, categorie_permis: str, date_expiration_permis: date, disponibilite: bool = True) -> Chauffeur:
        if not self.db.get(User, id_user):
            raise HTTPException(status_code=404, detail="Utilisateur introuvable.")
        if not self.db.get(Cooperative, id_cooperative):
            raise HTTPException(status_code=404, detail="Coopérative introuvable.")

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
            chauffeur_role = self.db.scalar(select(Role).where(Role.libelle == UserRole.CHAUFFEUR))
            if not chauffeur_role:
                raise HTTPException(status_code=500, detail="Le rôle chauffeur n'est pas configuré.")
            user = self.db.get(User, id_user)
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
        if fields.get("id_cooperative") is not None and not self.db.get(Cooperative, fields["id_cooperative"]):
            raise HTTPException(status_code=404, detail="Cooperative introuvable.")
        if "numero_permis" in fields and fields["numero_permis"]:
            new_permis = fields["numero_permis"].strip()
            if new_permis != item.numero_permis:
                existing = self.db.scalar(select(Chauffeur).where(Chauffeur.numero_permis == new_permis))
                if existing:
                    raise HTTPException(status_code=400, detail="Ce numéro de permis est déjà enregisté.")
                item.numero_permis = new_permis

        for key, value in fields.items():
            if key != "numero_permis" and value is not None and hasattr(Chauffeur, key):
                setattr(item, key, value.strip() if isinstance(value, str) else value)

        try:
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
        self.db.commit()
        self.db.refresh(item)
        return item

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
        chauffeur = self.get_chauffeur(chauffeur_id)
        vehicule = self.db.get(Vehicule, vehicule_id)
        if not vehicule:
            raise HTTPException(status_code=404, detail="Véhicule introuvable.")

        if chauffeur.id_cooperative != vehicule.id_cooperative:
            raise HTTPException(status_code=400, detail="Le chauffeur et le vehicule doivent appartenir a la meme cooperative.")
        if chauffeur.date_expiration_permis < date.today():
            raise HTTPException(status_code=422, detail="Le permis du chauffeur est expiré. Affectation impossible.")
        if date_fin is not None and date_fin <= date_debut:
            raise HTTPException(status_code=422, detail="La date de fin doit être postérieure à la date de début.")

        active_assignment = self.db.scalar(select(VehiculeChauffeur).where(
            VehiculeChauffeur.id_chauffeur == chauffeur_id,
            VehiculeChauffeur.is_active.is_(True),
        ))
        if active_assignment:
            raise HTTPException(status_code=409, detail="Ce chauffeur est déjà affecté à un véhicule actif.")

        assignment = VehiculeChauffeur(
            id_vehicule=vehicule_id,
            id_chauffeur=chauffeur_id,
            date_debut=date_debut,
            date_fin=date_fin,
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
