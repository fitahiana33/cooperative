from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.schemas.cooperative import (
    CooperativeCreate, CooperativeUpdate, CooperativeRead, AssociationCreate,
    MemberCreate, MemberUpdate, GareCooperativeRead, CooperativeMemberRead,
)
from app.schemas.common import PageResponse
from app.services.cooperative import CooperativeService
from app.api.controllers.authentication.dependencies import require_permission

router = APIRouter(prefix="/cooperatives", tags=["cooperatives"])

@router.get("", response_model=PageResponse[CooperativeRead])
def list_cooperatives(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = None,
    sort_by: str = "nom",
    sort_order: str = Query("asc", pattern="^(asc|desc)$"),
    _: User = Depends(require_permission("COOPERATIVE_READ")),
    db: Session = Depends(get_db),
):
    return CooperativeService(db).list_cooperatives(page=page, page_size=page_size, search=search, sort_by=sort_by, sort_order=sort_order)

@router.post("", response_model=CooperativeRead, status_code=status.HTTP_201_CREATED)
def create_cooperative(
    data: CooperativeCreate,
    _: User = Depends(require_permission("COOPERATIVE_CREATE")),
    db: Session = Depends(get_db),
):
    return CooperativeService(db).create_cooperative(
        nom=data.nom,
        adresse=data.adresse,
        telephone=data.telephone,
        email=data.email,
        sigle=data.sigle,
        numero_agrement=data.numero_agrement,
        ville=data.ville,
        description=data.description,
        responsable_id=data.responsable_id,
    )

@router.get("/{cooperative_id}", response_model=CooperativeRead)
def get_cooperative(
    cooperative_id: int,
    _: User = Depends(require_permission("COOPERATIVE_READ")),
    db: Session = Depends(get_db),
):
    return CooperativeService(db).get_cooperative(cooperative_id)

@router.put("/{cooperative_id}", response_model=CooperativeRead)
def update_cooperative(
    cooperative_id: int,
    data: CooperativeUpdate,
    _: User = Depends(require_permission("COOPERATIVE_UPDATE")),
    db: Session = Depends(get_db),
):
    return CooperativeService(db).update_cooperative(cooperative_id, **data.model_dump(exclude_unset=True))

@router.patch("/{cooperative_id}/toggle", response_model=CooperativeRead)
def toggle_cooperative(
    cooperative_id: int,
    _: User = Depends(require_permission("COOPERATIVE_UPDATE")),
    db: Session = Depends(get_db),
):
    return CooperativeService(db).toggle_cooperative(cooperative_id)

@router.delete("/{cooperative_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_cooperative(
    cooperative_id: int,
    _: User = Depends(require_permission("COOPERATIVE_DELETE")),
    db: Session = Depends(get_db),
):
    CooperativeService(db).delete_cooperative(cooperative_id)

@router.post("/{cooperative_id}/attach-gare/{gare_id}", status_code=status.HTTP_201_CREATED)
def attach_to_gare(
    cooperative_id: int,
    gare_id: int,
    data: AssociationCreate | None = None,
    _: User = Depends(require_permission("COOPERATIVE_UPDATE")),
    db: Session = Depends(get_db),
):
    return CooperativeService(db).attach_to_gare(
        gare_id, cooperative_id,
        date_debut=data.date_debut if data else None,
        date_fin=data.date_fin if data else None,
    )

@router.post("/{cooperative_id}/members", status_code=status.HTTP_201_CREATED)
def add_member(
    cooperative_id: int,
    data: MemberCreate,
    _: User = Depends(require_permission("COOPERATIVE_UPDATE")),
    db: Session = Depends(get_db),
):
    return CooperativeService(db).add_member(
        cooperative_id, data.id_user, role_cooperative=data.fonction or "MEMBRE",
        date_adhesion=data.date_adhesion, date_fin=data.date_fin,
    )

@router.get("/{cooperative_id}/gares", response_model=list[GareCooperativeRead])
def list_gare_associations(cooperative_id: int, _: User = Depends(require_permission("COOPERATIVE_READ")), db: Session = Depends(get_db)):
    return CooperativeService(db).list_gare_associations(cooperative_id)

@router.delete("/{cooperative_id}/attach-gare/{gare_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_from_gare(cooperative_id: int, gare_id: int, _: User = Depends(require_permission("COOPERATIVE_UPDATE")), db: Session = Depends(get_db)):
    CooperativeService(db).remove_from_gare(gare_id, cooperative_id)

@router.get("/{cooperative_id}/members", response_model=list[CooperativeMemberRead])
def list_members(cooperative_id: int, _: User = Depends(require_permission("COOPERATIVE_READ")), db: Session = Depends(get_db)):
    return CooperativeService(db).list_members(cooperative_id)

@router.put("/{cooperative_id}/members/{user_id}", response_model=CooperativeMemberRead)
def update_member(cooperative_id: int, user_id: int, data: MemberUpdate, _: User = Depends(require_permission("COOPERATIVE_UPDATE")), db: Session = Depends(get_db)):
    return CooperativeService(db).update_member(cooperative_id, user_id, **data.model_dump(exclude_unset=True))

@router.delete("/{cooperative_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_member(cooperative_id: int, user_id: int, _: User = Depends(require_permission("COOPERATIVE_UPDATE")), db: Session = Depends(get_db)):
    CooperativeService(db).remove_member(cooperative_id, user_id)
