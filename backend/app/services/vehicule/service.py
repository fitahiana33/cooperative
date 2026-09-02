import logging
from datetime import date
from pathlib import Path
from fastapi import HTTPException, status
from sqlalchemy import select
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

    def list_expired_documents(self, vehicule_id: int) -> list[VehiculeDocument]:
        self.get_vehicule(vehicule_id)
        return list(self.db.scalars(
            select(VehiculeDocument)
            .where(
                VehiculeDocument.id_vehicule == vehicule_id,
                VehiculeDocument.date_expiration.is_not(None),
                VehiculeDocument.date_expiration < date.today(),
            )
            .order_by(VehiculeDocument.date_expiration)
        ))

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
        for key, value in fields.items():
            if hasattr(VehiculeDocument, key) and value is not None:
                setattr(doc, key, value.strip() if isinstance(value, str) else value)
        try:
            self.db.commit()
            self.db.refresh(doc)
            return doc
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(status_code=400, detail="Informations de document invalides.")

    def list_vehicules(self, *, page=1, page_size=20, search=None, sort_by="immatriculation", sort_order="asc", id_cooperative=None):
        query = select(Vehicule)
        if id_cooperative:
            query = query.where(Vehicule.id_cooperative == id_cooperative)
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
        if not self.db.get(Modele, id_modele):
            raise HTTPException(status_code=404, detail="Modèle introuvable.")
        if not self.db.get(Cooperative, id_cooperative):
            raise HTTPException(status_code=404, detail="Coopérative introuvable.")

        existing = self.db.scalar(select(Vehicule).where(Vehicule.immatriculation == immatriculation.strip()))
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
        if fields.get("id_modele") is not None and not self.db.get(Modele, fields["id_modele"]):
            raise HTTPException(status_code=404, detail="Modele introuvable.")
        if fields.get("id_cooperative") is not None and not self.db.get(Cooperative, fields["id_cooperative"]):
            raise HTTPException(status_code=404, detail="Cooperative introuvable.")
        if "immatriculation" in fields and fields["immatriculation"]:
            new_imm = fields["immatriculation"].strip()
            if new_imm != item.immatriculation:
                existing = self.db.scalar(select(Vehicule).where(Vehicule.immatriculation == new_imm))
                if existing:
                    raise HTTPException(status_code=400, detail="Un véhicule avec cette immatriculation existe déjà.")
                item.immatriculation = new_imm

        for key, value in fields.items():
            if key != "immatriculation" and value is not None and hasattr(Vehicule, key):
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
            raise HTTPException(status_code=500, detail="Erreur lors de la mise à jour du véhicule.")

    def toggle_vehicule(self, vehicule_id: int) -> Vehicule:
        item = self.get_vehicule(vehicule_id)
        item.is_active = not item.is_active
        self.db.commit()
        self.db.refresh(item)
        return item

    def delete_vehicule(self, vehicule_id: int) -> None:
        item = self.get_vehicule(vehicule_id)
        document_paths = [document.fichier_path for document in item.documents]
        try:
            self.db.delete(item)
            self.db.commit()
            for file_path in document_paths:
                if file_path:
                    (DOCUMENT_UPLOAD_DIR / Path(file_path).name).unlink(missing_ok=True)
        except Exception:
            self.db.rollback()
            raise HTTPException(status_code=500, detail="Impossible de supprimer ce véhicule.")

    # --- Documents ---
    def add_document(self, vehicule_id: int, *, type_document: str, **fields) -> VehiculeDocument:
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
