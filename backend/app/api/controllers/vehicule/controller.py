from datetime import date
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.models.vehicule import VehiculeDocument
from app.schemas.vehicule import (
    VehiculeCreate,
    VehiculeUpdate,
    VehiculeRead,
    VehiculeDocumentCreate,
    VehiculeDocumentUpdate,
    VehiculeDocumentRead,
)
from app.schemas.vehicule.schema import DocumentType
from app.schemas.common import PageResponse
from app.services.vehicule import VehiculeService
from app.api.controllers.authentication.dependencies import require_permission

router = APIRouter(prefix="/vehicules", tags=["vehicules"])

DOCUMENT_UPLOAD_DIR = Path(__file__).resolve().parents[4] / "uploads" / "vehicules"
MAX_DOCUMENT_SIZE = 10 * 1024 * 1024
ALLOWED_DOCUMENT_EXTENSIONS = {
    ".pdf", ".png", ".jpg", ".jpeg", ".gif", ".webp",
    ".doc", ".docx", ".xls", ".xlsx",
}


def _remove_uploaded_file(file_path: str | None) -> None:
    if not file_path:
        return
    candidate = DOCUMENT_UPLOAD_DIR / Path(file_path).name
    if candidate.is_file():
        candidate.unlink()

@router.get("", response_model=PageResponse[VehiculeRead])
def list_vehicules(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = None,
    sort_by: str = "immatriculation",
    sort_order: str = Query("asc", pattern="^(asc|desc)$"),
    id_cooperative: int | None = None,
    _: User = Depends(require_permission("VEHICULE_READ")),
    db: Session = Depends(get_db),
):
    return VehiculeService(db).list_vehicules(
        page=page, page_size=page_size, search=search, sort_by=sort_by, sort_order=sort_order, id_cooperative=id_cooperative
    )

@router.post("", response_model=VehiculeRead, status_code=status.HTTP_201_CREATED)
def create_vehicule(
    data: VehiculeCreate,
    _: User = Depends(require_permission("VEHICULE_CREATE")),
    db: Session = Depends(get_db),
):
    return VehiculeService(db).create_vehicule(
        id_modele=data.id_modele,
        id_cooperative=data.id_cooperative,
        immatriculation=data.immatriculation,
        nombre_places=data.nombre_places,
        chevaux=data.chevaux,
        disponibilite=data.disponibilite,
        etat=data.etat,
        description=data.description,
    )

@router.get("/{vehicule_id}", response_model=VehiculeRead)
def get_vehicule(
    vehicule_id: int,
    _: User = Depends(require_permission("VEHICULE_READ")),
    db: Session = Depends(get_db),
):
    return VehiculeService(db).get_vehicule(vehicule_id)

@router.put("/{vehicule_id}", response_model=VehiculeRead)
def update_vehicule(
    vehicule_id: int,
    data: VehiculeUpdate,
    _: User = Depends(require_permission("VEHICULE_UPDATE")),
    db: Session = Depends(get_db),
):
    return VehiculeService(db).update_vehicule(vehicule_id, **data.model_dump(exclude_unset=True))

@router.patch("/{vehicule_id}/toggle", response_model=VehiculeRead)
def toggle_vehicule(
    vehicule_id: int,
    _: User = Depends(require_permission("VEHICULE_UPDATE")),
    db: Session = Depends(get_db),
):
    return VehiculeService(db).toggle_vehicule(vehicule_id)

@router.delete("/{vehicule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vehicule(
    vehicule_id: int,
    _: User = Depends(require_permission("VEHICULE_DELETE")),
    db: Session = Depends(get_db),
):
    VehiculeService(db).delete_vehicule(vehicule_id)

# --- Documents du véhicule ---
@router.post("/{vehicule_id}/documents/upload", response_model=VehiculeDocumentRead, status_code=status.HTTP_201_CREATED)
async def upload_document(
    vehicule_id: int,
    type_document: DocumentType = Form(...),
    numero_document: str | None = Form(None),
    date_delivrance: date | None = Form(None),
    date_expiration: date | None = Form(None),
    is_valid: bool = Form(True),
    file: UploadFile = File(...),
    _: User = Depends(require_permission("VEHICULE_UPDATE")),
    db: Session = Depends(get_db),
):
    if date_delivrance and date_expiration and date_expiration < date_delivrance:
        raise HTTPException(
            status_code=422,
            detail="La date d'expiration doit être postérieure ou égale à la date de délivrance.",
        )

    extension = Path(file.filename or "").suffix.lower()
    if extension not in ALLOWED_DOCUMENT_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Format de fichier non accepté. Utilisez PDF, image, Word ou Excel.",
        )

    content = await file.read(MAX_DOCUMENT_SIZE + 1)
    if len(content) > MAX_DOCUMENT_SIZE:
        raise HTTPException(status_code=413, detail="Le fichier ne doit pas dépasser 10 Mo.")

    DOCUMENT_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    stored_name = f"{uuid4().hex}{extension}"
    stored_file = DOCUMENT_UPLOAD_DIR / stored_name
    stored_file.write_bytes(content)

    try:
        return VehiculeService(db).add_document(
            vehicule_id,
            type_document=type_document,
            numero_document=numero_document,
            date_delivrance=date_delivrance,
            date_expiration=date_expiration,
            fichier_path=f"/uploads/vehicules/{stored_name}",
            is_valid=is_valid,
        )
    except Exception:
        stored_file.unlink(missing_ok=True)
        raise


@router.post("/{vehicule_id}/documents", response_model=VehiculeDocumentRead, status_code=status.HTTP_201_CREATED)
def add_document(
    vehicule_id: int,
    data: VehiculeDocumentCreate,
    _: User = Depends(require_permission("VEHICULE_UPDATE")),
    db: Session = Depends(get_db),
):
    return VehiculeService(db).add_document(vehicule_id, **data.model_dump())

@router.get("/{vehicule_id}/documents", response_model=list[VehiculeDocumentRead])
def list_documents(vehicule_id: int, _: User = Depends(require_permission("VEHICULE_READ")), db: Session = Depends(get_db)):
    return VehiculeService(db).list_documents(vehicule_id)

@router.get("/{vehicule_id}/documents/expired", response_model=list[VehiculeDocumentRead])
def list_expired_documents(
    vehicule_id: int,
    _: User = Depends(require_permission("VEHICULE_READ")),
    db: Session = Depends(get_db),
):
    return VehiculeService(db).list_expired_documents(vehicule_id)

@router.put("/documents/{document_id}", response_model=VehiculeDocumentRead)
def update_document(document_id: int, data: VehiculeDocumentUpdate, _: User = Depends(require_permission("VEHICULE_UPDATE")), db: Session = Depends(get_db)):
    return VehiculeService(db).update_document(document_id, **data.model_dump(exclude_unset=True))

@router.patch("/documents/{document_id}/toggle", response_model=VehiculeDocumentRead)
def toggle_document(document_id: int, _: User = Depends(require_permission("VEHICULE_UPDATE")), db: Session = Depends(get_db)):
    return VehiculeService(db).toggle_document(document_id)

@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: int,
    _: User = Depends(require_permission("VEHICULE_UPDATE")),
    db: Session = Depends(get_db),
):
    document = db.get(VehiculeDocument, document_id)
    file_path = document.fichier_path if document else None
    VehiculeService(db).delete_document(document_id)
    _remove_uploaded_file(file_path)
