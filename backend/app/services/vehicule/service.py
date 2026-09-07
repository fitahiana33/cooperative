import logging
from datetime import date, timedelta
from pathlib import Path
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.vehicule import Vehicule, VehiculeDocument, VehiculeChauffeur
from app.models.modele import Modele
from app.models.cooperative import Cooperative
from app.core.pagination import paginate

logger = logging.getLogger("cooperative.vehicule")
DOCUMENT_UPLOAD_DIR = Path(__file__).resolve().parents[3] / "uploads" / "vehicules"

class VehiculeService:
    def __init__(self, db: Session):
        self.db = db

    def list_documents(self, vehicule_id: int) -> list[VehiculeDocument]:
        self.get_vehicule(vehicule_id)
        return list(self.db.scalars(select(VehiculeDocument).where(
            VehiculeDocument.id_vehicule == vehicule_id,
        ).order_by(VehiculeDocument.date_expiration)))

    def get_document(self, document_id: int) -> VehiculeDocument:
        document = self.db.get(VehiculeDocument, document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document introuvable.")
        return document

    def list_expired_documents(self, vehicule_id: int) -> list[VehiculeDocument]:
        self.get_vehicule(vehicule_id)
        return list(self.db.scalars(
            select(VehiculeDocument)
            .where(
                VehiculeDocument.id_vehicule == vehicule_id,
                VehiculeDocument.date_expiration.is_not(None),
                VehiculeDocument.date_expiration < date.today(),
                VehiculeDocument.is_active.is_(True),
            )
            .order_by(VehiculeDocument.date_expiration)
        ))

    def list_expiring_documents(self, vehicule_id: int, *, days: int = 30) -> list[VehiculeDocument]:
        self.get_vehicule(vehicule_id)
        today = date.today()
        return list(self.db.scalars(
            select(VehiculeDocument)
            .where(
                VehiculeDocument.id_vehicule == vehicule_id,
                VehiculeDocument.is_active.is_(True),
                VehiculeDocument.date_expiration >= today,
                VehiculeDocument.date_expiration <= today + timedelta(days=days),
            )
            .order_by(VehiculeDocument.date_expiration)
        ))

    def list_all_expiring_documents(
        self,
        *,
        days: int | None = None,
        cooperative_ids: set[int] | None = None,
    ) -> list[VehiculeDocument]:
        """Return active fleet documents that are expired or close to expiry."""
        today = date.today()
        statement = select(VehiculeDocument).join(Vehicule)
        statement = statement.where(
            VehiculeDocument.is_active.is_(True),
            Vehicule.is_active.is_(True),
            VehiculeDocument.date_expiration.is_not(None),
        )
        if days is None:
            statement = statement.where(VehiculeDocument.date_expiration < today)
        else:
            statement = statement.where(
                VehiculeDocument.date_expiration >= today,
                VehiculeDocument.date_expiration <= today + timedelta(days=days),
            )
        if cooperative_ids is not None:
            statement = statement.where(Vehicule.id_cooperative.in_(cooperative_ids))
        return list(self.db.scalars(statement.order_by(VehiculeDocument.date_expiration)))

    def update_document(self, document_id: int, **fields) -> VehiculeDocument:
        doc = self.db.get(VehiculeDocument, document_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document introuvable.")

        next_issue_date = fields.get("date_delivrance", doc.date_delivrance)
        next_expiration_date = fields.get("date_expiration", doc.date_expiration)
        if (
            next_issue_date is not None
            and next_expiration_date is not None
            and next_expiration_date < next_issue_date
        ):
            raise HTTPException(
                status_code=422,
                detail="La date d'expiration doit être postérieure ou égale à la date de délivrance.",
            )
        nullable_fields = {"numero_document", "date_delivrance", "date_expiration"}
        for key, value in fields.items():
            if hasattr(VehiculeDocument, key) and (value is not None or key in nullable_fields):
                setattr(doc, key, value.strip() if isinstance(value, str) else value)
        try:
            self.db.commit()
            self.db.refresh(doc)
            return doc
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(status_code=400, detail="Informations de document invalides.")

    def list_vehicules(self, *, page=1, page_size=20, search=None, sort_by="immatriculation", sort_order="asc", id_cooperative=None, cooperative_ids: set[int] | None = None):
        query = select(Vehicule)
        if id_cooperative is not None:
            query = query.where(Vehicule.id_cooperative == id_cooperative)
        if cooperative_ids is not None:
            query = query.where(Vehicule.id_cooperative.in_(cooperative_ids))
        return paginate(
            self.db,
            Vehicule,
            statement=query,
            page=page,
            page_size=page_size,
            search=search,
            search_fields=("immatriculation", "etat", "description"),
            sort_by=sort_by,
            sort_fields=("immatriculation", "nombre_places", "etat", "created_at"),
            sort_order=sort_order,
        )

    def get_vehicule(self, vehicule_id: int) -> Vehicule:
        item = self.db.get(Vehicule, vehicule_id)
        if not item:
            raise HTTPException(status_code=404, detail="Véhicule introuvable.")
        return item

    def create_vehicule(self, *, id_modele: int, id_cooperative: int, immatriculation: str, nombre_places: int, **fields) -> Vehicule:
        modele = self.db.get(Modele, id_modele)
        if not modele:
            raise HTTPException(status_code=404, detail="Modèle introuvable.")
        if not modele.is_active or not modele.marque.is_active:
            raise HTTPException(status_code=422, detail="Le modèle sélectionné est inactif.")
        cooperative = self.db.get(Cooperative, id_cooperative)
        if not cooperative:
            raise HTTPException(status_code=404, detail="Coopérative introuvable.")
        if not cooperative.is_active:
            raise HTTPException(status_code=422, detail="La coopérative sélectionnée est inactive.")

        if fields.get("etat") == "HORS_SERVICE":
            fields["disponibilite"] = False

        existing = self.db.scalar(select(Vehicule).where(
            func.lower(Vehicule.immatriculation) == immatriculation.strip().lower(),
        ))
        if existing:
            raise HTTPException(status_code=400, detail="Un véhicule avec cette immatriculation existe déjà.")

        item = Vehicule(
            id_modele=id_modele,
            id_cooperative=id_cooperative,
            immatriculation=immatriculation.strip(),
            nombre_places=nombre_places,
            **{k: v for k, v in fields.items() if hasattr(Vehicule, k)},
        )
        try:
            self.db.add(item)
            self.db.commit()
            self.db.refresh(item)
            return item
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(status_code=400, detail="Les informations du véhicule sont invalides.")
        except Exception:
            self.db.rollback()
            logger.exception("Erreur création véhicule immatriculation=%s", immatriculation)
            raise HTTPException(status_code=500, detail="Une erreur est survenue lors de la création du véhicule.")

    def update_vehicule(self, vehicule_id: int, **fields) -> Vehicule:
        item = self.get_vehicule(vehicule_id)
        if fields.get("id_modele") is not None:
            modele = self.db.get(Modele, fields["id_modele"])
            if not modele:
                raise HTTPException(status_code=404, detail="Modèle introuvable.")
            if not modele.is_active or not modele.marque.is_active:
                raise HTTPException(status_code=422, detail="Le modèle sélectionné est inactif.")
        if fields.get("id_cooperative") is not None:
            cooperative = self.db.get(Cooperative, fields["id_cooperative"])
            if not cooperative:
                raise HTTPException(status_code=404, detail="Coopérative introuvable.")
            if not cooperative.is_active:
                raise HTTPException(status_code=422, detail="La coopérative sélectionnée est inactive.")
            if cooperative.id != item.id_cooperative and any(
                assignment.is_active for assignment in item.chauffeurs_assignments
            ):
                raise HTTPException(
                    status_code=409,
                    detail="Le véhicule ne peut pas changer de coopérative tant qu'il possède une affectation active.",
                )
        if fields.get("etat") == "HORS_SERVICE":
            fields["disponibilite"] = False
        elif fields.get("disponibilite") is True and item.etat == "HORS_SERVICE":
            raise HTTPException(
                status_code=422,
                detail="Un vÃ©hicule hors service ne peut pas Ãªtre rendu disponible.",
            )

        if "immatriculation" in fields and fields["immatriculation"]:
            new_imm = fields["immatriculation"].strip()
            if new_imm != item.immatriculation:
                existing = self.db.scalar(select(Vehicule).where(
                    func.lower(Vehicule.immatriculation) == new_imm.lower(),
                ))
                if existing:
                    raise HTTPException(status_code=400, detail="Un véhicule avec cette immatriculation existe déjà.")
                item.immatriculation = new_imm

        nullable_fields = {"chevaux", "description"}
        should_close_assignments = fields.get("is_active") is False and item.is_active
        for key, value in fields.items():
            if key != "immatriculation" and (value is not None or key in nullable_fields) and hasattr(Vehicule, key):
                setattr(item, key, value.strip() if isinstance(value, str) else value)

        try:
            if should_close_assignments:
                self._close_vehicle_assignments(item.id)
            self.db.commit()
            self.db.refresh(item)
            return item
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(status_code=400, detail="Les informations fournies sont invalides.")
        except Exception:
            self.db.rollback()
            raise HTTPException(status_code=500, detail="Erreur lors de la mise à jour du véhicule.")

    def toggle_vehicule(self, vehicule_id: int) -> Vehicule:
        item = self.get_vehicule(vehicule_id)
        item.is_active = not item.is_active
        try:
            if not item.is_active:
                self._close_vehicle_assignments(item.id)
            self.db.commit()
            self.db.refresh(item)
            return item
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(status_code=409, detail="Impossible de modifier l'état du véhicule.")

    def _close_vehicle_assignments(self, vehicule_id: int) -> None:
        today = date.today()
        assignments = self.db.scalars(select(VehiculeChauffeur).where(
            VehiculeChauffeur.id_vehicule == vehicule_id,
            VehiculeChauffeur.is_active.is_(True),
        ))
        for assignment in assignments:
            assignment.is_active = False
            assignment.date_fin = max(today, assignment.date_debut)

    def delete_vehicule(self, vehicule_id: int) -> None:
        item = self.get_vehicule(vehicule_id)
        document_paths = [document.fichier_path for document in item.documents]
        try:
            self.db.delete(item)
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(
                status_code=409,
                detail="Impossible de supprimer un véhicule encore utilisé ou possédant un historique.",
            )
        except Exception:
            self.db.rollback()
            logger.exception("Erreur interne suppression véhicule: id=%s", vehicule_id)
            raise HTTPException(status_code=500, detail="Impossible de supprimer ce véhicule.")
        for file_path in document_paths:
            if file_path:
                try:
                    (DOCUMENT_UPLOAD_DIR / Path(file_path).name).unlink(missing_ok=True)
                except OSError:
                    logger.warning("Fichier documentaire non supprimé après suppression du véhicule: %s", file_path)

    # --- Documents ---
    def add_document(
        self,
        vehicule_id: int,
        *,
        type_document: str,
        fichier_path: str | None = None,
        **fields,
    ) -> VehiculeDocument:
        self.get_vehicule(vehicule_id)
        issue_date = fields.get("date_delivrance")
        expiration_date = fields.get("date_expiration")
        if (
            issue_date is not None
            and expiration_date is not None
            and expiration_date < issue_date
        ):
            raise HTTPException(
                status_code=422,
                detail="La date d'expiration doit être postérieure ou égale à la date de délivrance.",
            )
        doc = VehiculeDocument(
            id_vehicule=vehicule_id,
            type_document=type_document,
            fichier_path=fichier_path,
            **{k: v for k, v in fields.items() if hasattr(VehiculeDocument, k)},
        )
        try:
            self.db.add(doc)
            self.db.commit()
            self.db.refresh(doc)
            return doc
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(status_code=400, detail="Informations de document invalides.")

    def toggle_document(self, document_id: int) -> VehiculeDocument:
        doc = self.db.get(VehiculeDocument, document_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document introuvable.")
        doc.is_active = not doc.is_active
        self.db.commit()
        self.db.refresh(doc)
        return doc

    def delete_document(self, document_id: int) -> None:
        doc = self.db.get(VehiculeDocument, document_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document introuvable.")
        self.db.delete(doc)
        self.db.commit()
