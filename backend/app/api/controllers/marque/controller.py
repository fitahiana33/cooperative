from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.schemas.marque import MarqueCreate, MarqueUpdate, MarqueRead
from app.schemas.common import PageResponse
from app.services.marque import MarqueService
from app.api.controllers.authentication.dependencies import require_permission

router = APIRouter(prefix="/marques", tags=["marques"])

@router.get("", response_model=PageResponse[MarqueRead])
def list_marques(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = None,
    sort_by: str = "nom",
    sort_order: str = Query("asc", pattern="^(asc|desc)$"),
    _: User = Depends(require_permission("VEHICULE_READ")),
    db: Session = Depends(get_db),
):
    return MarqueService(db).list_marques(page=page, page_size=page_size, search=search, sort_by=sort_by, sort_order=sort_order)

@router.post("", response_model=MarqueRead, status_code=status.HTTP_201_CREATED)
def create_marque(
    data: MarqueCreate,
    _: User = Depends(require_permission("VEHICULE_CREATE")),
    db: Session = Depends(get_db),
):
    return MarqueService(db).create_marque(nom=data.nom, description=data.description)

@router.get("/{marque_id}", response_model=MarqueRead)
def get_marque(
    marque_id: int,
    _: User = Depends(require_permission("VEHICULE_READ")),
    db: Session = Depends(get_db),
):
    return MarqueService(db).get_marque(marque_id)

@router.put("/{marque_id}", response_model=MarqueRead)
def update_marque(
    marque_id: int,
    data: MarqueUpdate,
    _: User = Depends(require_permission("VEHICULE_UPDATE")),
    db: Session = Depends(get_db),
):
    return MarqueService(db).update_marque(marque_id, **data.model_dump(exclude_unset=True))

@router.patch("/{marque_id}/toggle", response_model=MarqueRead)
def toggle_marque(
    marque_id: int,
    _: User = Depends(require_permission("VEHICULE_UPDATE")),
    db: Session = Depends(get_db),
):
    return MarqueService(db).toggle_marque(marque_id)

@router.delete("/{marque_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_marque(
    marque_id: int,
    _: User = Depends(require_permission("VEHICULE_DELETE")),
    db: Session = Depends(get_db),
):
    MarqueService(db).delete_marque(marque_id)
