from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.cooperative import (
    CooperativeCreate, CooperativeUpdate, CooperativeRead, AssociationCreate,
    MemberCreate, MemberUpdate, GareCooperativeRead, CooperativeMemberRead,
)
from app.schemas.common import PageResponse
from app.schemas.user import UserRead
from app.schemas.gare import GareRead
from app.services.cooperative import CooperativeService
from app.api.controllers.authentication.dependencies import (
    ensure_cooperative_access,
    get_user_cooperative_ids,
    has_global_cooperative_access,
    has_active_role,
    require_permission,
    require_roles,
)

router = APIRouter(prefix="/cooperatives", tags=["cooperatives"])

@router.get("", response_model=PageResponse[CooperativeRead])
def list_cooperatives(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None, max_length=100),
    sort_by: str = Query("nom", pattern="^(nom|sigle|ville|created_at)$"),
    sort_order: str = Query("asc", pattern="^(asc|desc)$"),
    current_user: User = Depends(require_permission("COOPERATIVE_READ")),
    db: Session = Depends(get_db),
):
    cooperative_ids = (
        None
        if has_global_cooperative_access(current_user)
        else get_user_cooperative_ids(db, current_user)
    )
    return CooperativeService(db).list_cooperatives(
        page=page,
        page_size=page_size,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        cooperative_ids=cooperative_ids,
    )

@router.get("/eligible-responsables", response_model=list[UserRead])
def list_eligible_responsables(
    _: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    return CooperativeService(db).list_eligible_responsables()

@router.post("", response_model=CooperativeRead, status_code=status.HTTP_201_CREATED)
def create_cooperative(
    data: CooperativeCreate,
    _: User = Depends(require_roles(UserRole.ADMIN)),
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
    current_user: User = Depends(require_permission("COOPERATIVE_READ")),
    db: Session = Depends(get_db),
):
    ensure_cooperative_access(db, current_user, cooperative_id)
    return CooperativeService(db).get_cooperative(cooperative_id)

@router.get("/{cooperative_id}/eligible-chauffeur-users", response_model=list[UserRead])
def list_eligible_chauffeur_users(
    cooperative_id: int,
    current_user: User = Depends(require_permission("CHAUFFEUR_CREATE")),
    db: Session = Depends(get_db),
):
    ensure_cooperative_access(db, current_user, cooperative_id)
    return CooperativeService(db).list_eligible_chauffeur_users(cooperative_id)

@router.get("/{cooperative_id}/eligible-members", response_model=list[UserRead])
def list_eligible_members(
    cooperative_id: int,
    current_user: User = Depends(require_permission("COOPERATIVE_UPDATE")),
    db: Session = Depends(get_db),
):
    ensure_cooperative_access(db, current_user, cooperative_id)
    return CooperativeService(db).list_eligible_members(cooperative_id)

@router.get("/{cooperative_id}/available-gares", response_model=list[GareRead])
def list_available_gares(
    cooperative_id: int,
    current_user: User = Depends(require_permission("COOPERATIVE_UPDATE")),
    db: Session = Depends(get_db),
):
    ensure_cooperative_access(db, current_user, cooperative_id)
    return CooperativeService(db).list_available_gares(cooperative_id)

@router.put("/{cooperative_id}", response_model=CooperativeRead)
def update_cooperative(
    cooperative_id: int,
    data: CooperativeUpdate,
    current_user: User = Depends(require_permission("COOPERATIVE_UPDATE")),
    db: Session = Depends(get_db),
):
    ensure_cooperative_access(db, current_user, cooperative_id)
    fields = data.model_dump(exclude_unset=True)
    if "responsable_id" in fields and not has_active_role(current_user, UserRole.ADMIN):
        raise HTTPException(status_code=403, detail="Seul un administrateur peut changer le responsable.")
    return CooperativeService(db).update_cooperative(cooperative_id, **fields)

@router.patch("/{cooperative_id}/toggle", response_model=CooperativeRead)
def toggle_cooperative(
    cooperative_id: int,
    current_user: User = Depends(require_permission("COOPERATIVE_UPDATE")),
    db: Session = Depends(get_db),
):
    ensure_cooperative_access(db, current_user, cooperative_id)
    return CooperativeService(db).toggle_cooperative(cooperative_id)

@router.delete("/{cooperative_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_cooperative(
    cooperative_id: int,
    _: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    CooperativeService(db).delete_cooperative(cooperative_id)

@router.post("/{cooperative_id}/attach-gare/{gare_id}", response_model=GareCooperativeRead, status_code=status.HTTP_201_CREATED)
def attach_to_gare(
    cooperative_id: int,
    gare_id: int,
    data: AssociationCreate | None = None,
    current_user: User = Depends(require_permission("COOPERATIVE_UPDATE")),
    db: Session = Depends(get_db),
):
    ensure_cooperative_access(db, current_user, cooperative_id)
    return CooperativeService(db).attach_to_gare(
        gare_id, cooperative_id,
        date_debut=data.date_debut if data else None,
        date_fin=data.date_fin if data else None,
    )

@router.post("/{cooperative_id}/members", response_model=CooperativeMemberRead, status_code=status.HTTP_201_CREATED)
def add_member(
    cooperative_id: int,
    data: MemberCreate,
    current_user: User = Depends(require_permission("COOPERATIVE_UPDATE")),
    db: Session = Depends(get_db),
):
    ensure_cooperative_access(db, current_user, cooperative_id)
    return CooperativeService(db).add_member(
        cooperative_id, data.id_user, role_cooperative=data.fonction or "MEMBRE",
        date_adhesion=data.date_adhesion, date_fin=data.date_fin,
    )

@router.get("/{cooperative_id}/gares", response_model=list[GareCooperativeRead])
def list_gare_associations(cooperative_id: int, current_user: User = Depends(require_permission("COOPERATIVE_READ")), db: Session = Depends(get_db)):
    ensure_cooperative_access(db, current_user, cooperative_id)
    return CooperativeService(db).list_gare_associations(cooperative_id)

@router.delete("/{cooperative_id}/attach-gare/{gare_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_from_gare(cooperative_id: int, gare_id: int, current_user: User = Depends(require_permission("COOPERATIVE_UPDATE")), db: Session = Depends(get_db)):
    ensure_cooperative_access(db, current_user, cooperative_id)
    CooperativeService(db).remove_from_gare(gare_id, cooperative_id)

@router.get("/{cooperative_id}/members", response_model=list[CooperativeMemberRead])
def list_members(cooperative_id: int, current_user: User = Depends(require_permission("COOPERATIVE_READ")), db: Session = Depends(get_db)):
    ensure_cooperative_access(db, current_user, cooperative_id)
    return CooperativeService(db).list_members(cooperative_id)

@router.put("/{cooperative_id}/members/{user_id}", response_model=CooperativeMemberRead)
def update_member(cooperative_id: int, user_id: int, data: MemberUpdate, current_user: User = Depends(require_permission("COOPERATIVE_UPDATE")), db: Session = Depends(get_db)):
    ensure_cooperative_access(db, current_user, cooperative_id)
    return CooperativeService(db).update_member(cooperative_id, user_id, **data.model_dump(exclude_unset=True))

@router.delete("/{cooperative_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_member(cooperative_id: int, user_id: int, current_user: User = Depends(require_permission("COOPERATIVE_UPDATE")), db: Session = Depends(get_db)):
    ensure_cooperative_access(db, current_user, cooperative_id)
    CooperativeService(db).remove_member(cooperative_id, user_id)
