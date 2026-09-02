from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.schemas.modele import ModeleCreate, ModeleUpdate, ModeleRead
from app.schemas.common import PageResponse
from app.services.modele import ModeleService
from app.api.controllers.authentication.dependencies import require_permission

router = APIRouter(prefix="/modeles", tags=["modeles"])

@router.get("", response_model=PageResponse[ModeleRead])
def list_modeles(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = None,
    sort_by: str = "nom",
    sort_order: str = Query("asc", pattern="^(asc|desc)$"),
    id_marque: int | None = None,
    _: User = Depends(require_permission("VEHICULE_READ")),
    db: Session = Depends(get_db),
):
    return ModeleService(db).list_modeles(page=page, page_size=page_size, search=search, sort_by=sort_by, sort_order=sort_order, id_marque=id_marque)

@router.post("", response_model=ModeleRead, status_code=status.HTTP_201_CREATED)
def create_modele(
    data: ModeleCreate,
    _: User = Depends(require_permission("VEHICULE_CREATE")),
    db: Session = Depends(get_db),
):
    return ModeleService(db).create_modele(id_marque=data.id_marque, nom=data.nom, description=data.description)

@router.get("/{modele_id}", response_model=ModeleRead)
def get_modele(
    modele_id: int,
    _: User = Depends(require_permission("VEHICULE_READ")),
    db: Session = Depends(get_db),
):
    return ModeleService(db).get_modele(modele_id)

@router.put("/{modele_id}", response_model=ModeleRead)
def update_modele(
    modele_id: int,
    data: ModeleUpdate,
    _: User = Depends(require_permission("VEHICULE_UPDATE")),
    db: Session = Depends(get_db),
):
    return ModeleService(db).update_modele(modele_id, **data.model_dump(exclude_unset=True))

@router.patch("/{modele_id}/toggle", response_model=ModeleRead)
def toggle_modele(
    modele_id: int,
    _: User = Depends(require_permission("VEHICULE_UPDATE")),
    db: Session = Depends(get_db),
):
    return ModeleService(db).toggle_modele(modele_id)

@router.delete("/{modele_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_modele(
    modele_id: int,
    _: User = Depends(require_permission("VEHICULE_DELETE")),
    db: Session = Depends(get_db),
):
    ModeleService(db).delete_modele(modele_id)
