from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.schemas.chauffeur import (
    ChauffeurCreate,
    ChauffeurUpdate,
    ChauffeurRead,
    VehiculeChauffeurAssign,
    VehiculeChauffeurClose,
    VehiculeChauffeurRead,
)
from app.schemas.common import PageResponse
from app.services.chauffeur import ChauffeurService
from app.api.controllers.authentication.dependencies import require_permission

router = APIRouter(prefix="/chauffeurs", tags=["chauffeurs"])

@router.get("", response_model=PageResponse[ChauffeurRead])
def list_chauffeurs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = None,
    sort_by: str = "created_at",
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    id_cooperative: int | None = None,
    _: User = Depends(require_permission("CHAUFFEUR_READ")),
    db: Session = Depends(get_db),
):
    return ChauffeurService(db).list_chauffeurs(
        page=page, page_size=page_size, search=search, sort_by=sort_by, sort_order=sort_order, id_cooperative=id_cooperative
    )

@router.post("", response_model=ChauffeurRead, status_code=status.HTTP_201_CREATED)
def create_chauffeur(
    data: ChauffeurCreate,
    _: User = Depends(require_permission("CHAUFFEUR_CREATE")),
    db: Session = Depends(get_db),
):
    return ChauffeurService(db).create_chauffeur(
        id_user=data.id_user,
        id_cooperative=data.id_cooperative,
        numero_permis=data.numero_permis,
        categorie_permis=data.categorie_permis,
        date_expiration_permis=data.date_expiration_permis,
        disponibilite=data.disponibilite,
    )

@router.get("/{chauffeur_id}", response_model=ChauffeurRead)
def get_chauffeur(
    chauffeur_id: int,
    _: User = Depends(require_permission("CHAUFFEUR_READ")),
    db: Session = Depends(get_db),
):
    return ChauffeurService(db).get_chauffeur(chauffeur_id)

@router.put("/{chauffeur_id}", response_model=ChauffeurRead)
def update_chauffeur(
    chauffeur_id: int,
    data: ChauffeurUpdate,
    _: User = Depends(require_permission("CHAUFFEUR_UPDATE")),
    db: Session = Depends(get_db),
):
    return ChauffeurService(db).update_chauffeur(chauffeur_id, **data.model_dump(exclude_unset=True))

@router.patch("/{chauffeur_id}/toggle", response_model=ChauffeurRead)
def toggle_chauffeur(
    chauffeur_id: int,
    _: User = Depends(require_permission("CHAUFFEUR_UPDATE")),
    db: Session = Depends(get_db),
):
    return ChauffeurService(db).toggle_chauffeur(chauffeur_id)

@router.delete("/{chauffeur_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_chauffeur(
    chauffeur_id: int,
    _: User = Depends(require_permission("CHAUFFEUR_DELETE")),
    db: Session = Depends(get_db),
):
    ChauffeurService(db).delete_chauffeur(chauffeur_id)

@router.post("/{chauffeur_id}/assign-vehicule", response_model=VehiculeChauffeurRead, status_code=status.HTTP_201_CREATED)
def assign_to_vehicule(
    chauffeur_id: int,
    data: VehiculeChauffeurAssign,
    _: User = Depends(require_permission("CHAUFFEUR_UPDATE")),
    db: Session = Depends(get_db),
):
    return ChauffeurService(db).assign_to_vehicule(
        chauffeur_id=chauffeur_id,
        vehicule_id=data.id_vehicule,
        date_debut=data.date_debut,
        date_fin=data.date_fin,
    )

@router.get("/{chauffeur_id}/vehicules", response_model=list[VehiculeChauffeurRead])
def list_assignments(chauffeur_id: int, _: User = Depends(require_permission("CHAUFFEUR_READ")), db: Session = Depends(get_db)):
    return ChauffeurService(db).list_assignments(chauffeur_id)

@router.post("/{chauffeur_id}/vehicules/{vehicule_id}/close", status_code=status.HTTP_204_NO_CONTENT)
def close_assignment(
    chauffeur_id: int,
    vehicule_id: int,
    data: VehiculeChauffeurClose,
    _: User = Depends(require_permission("CHAUFFEUR_UPDATE")),
    db: Session = Depends(get_db),
):
    ChauffeurService(db).close_assignment(chauffeur_id, vehicule_id, data.date_debut)
