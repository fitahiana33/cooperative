from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.api.controllers.authentication.dependencies import ensure_cooperative_access, get_user_cooperative_ids, has_global_cooperative_access, require_permission, require_roles
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.common import PageResponse
from app.schemas.itineraire import ItineraireCooperativeCreate, ItineraireCooperativeRead, ItineraireCreate, ItineraireRead, ItineraireUpdate
from app.services.itineraire import ItineraireService

router = APIRouter(prefix="/itineraires", tags=["itineraires"])


@router.get("", response_model=PageResponse[ItineraireRead])
def list_itineraires(
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None, max_length=100),
    sort_by: str = Query("created_at", pattern="^(created_at|distance_km|duree_estimee_minutes)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    current_user: User = Depends(require_permission("ITINERAIRE_READ")), db: Session = Depends(get_db),
):
    cooperative_ids = None if has_global_cooperative_access(current_user) else get_user_cooperative_ids(db, current_user)
    return ItineraireService(db).list_itineraires(page=page, page_size=page_size, search=search, sort_by=sort_by, sort_order=sort_order, cooperative_ids=cooperative_ids)


@router.post("", response_model=ItineraireRead, status_code=status.HTTP_201_CREATED)
def create_itineraire(data: ItineraireCreate, _: User = Depends(require_roles(UserRole.ADMIN)), db: Session = Depends(get_db)):
    return ItineraireService(db).create_itineraire(**data.model_dump())


@router.get("/{itineraire_id}", response_model=ItineraireRead)
def get_itineraire(itineraire_id: int, current_user: User = Depends(require_permission("ITINERAIRE_READ")), db: Session = Depends(get_db)):
    cooperative_ids = None if has_global_cooperative_access(current_user) else get_user_cooperative_ids(db, current_user)
    return ItineraireService(db).get_itineraire(itineraire_id, cooperative_ids=cooperative_ids)


@router.put("/{itineraire_id}", response_model=ItineraireRead)
def update_itineraire(itineraire_id: int, data: ItineraireUpdate, _: User = Depends(require_roles(UserRole.ADMIN)), db: Session = Depends(get_db)):
    return ItineraireService(db).update_itineraire(itineraire_id, **data.model_dump(exclude_unset=True))


@router.patch("/{itineraire_id}/toggle", response_model=ItineraireRead)
def toggle_itineraire(itineraire_id: int, _: User = Depends(require_roles(UserRole.ADMIN)), db: Session = Depends(get_db)):
    return ItineraireService(db).toggle_itineraire(itineraire_id)


@router.delete("/{itineraire_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_itineraire(itineraire_id: int, _: User = Depends(require_roles(UserRole.ADMIN)), db: Session = Depends(get_db)):
    ItineraireService(db).delete_itineraire(itineraire_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{itineraire_id}/cooperatives", response_model=list[ItineraireCooperativeRead])
def list_itineraire_cooperatives(itineraire_id: int, current_user: User = Depends(require_permission("ITINERAIRE_READ")), db: Session = Depends(get_db)):
    cooperative_ids = None if has_global_cooperative_access(current_user) else get_user_cooperative_ids(db, current_user)
    return ItineraireService(db).list_cooperatives(itineraire_id, cooperative_ids=cooperative_ids)


@router.post("/{itineraire_id}/cooperatives/{cooperative_id}", response_model=ItineraireCooperativeRead, status_code=status.HTTP_201_CREATED)
def attach_itineraire_cooperative(
    itineraire_id: int, cooperative_id: int, data: ItineraireCooperativeCreate | None = None,
    current_user: User = Depends(require_permission("ITINERAIRE_COOPERATIVE_MANAGE")), db: Session = Depends(get_db),
):
    ensure_cooperative_access(db, current_user, cooperative_id)
    values = data.model_dump(exclude_unset=True) if data else {}
    return ItineraireService(db).attach_cooperative(itineraire_id, cooperative_id, **values)


@router.delete("/{itineraire_id}/cooperatives/{cooperative_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_itineraire_cooperative(
    itineraire_id: int, cooperative_id: int,
    current_user: User = Depends(require_permission("ITINERAIRE_COOPERATIVE_MANAGE")), db: Session = Depends(get_db),
):
    ensure_cooperative_access(db, current_user, cooperative_id)
    ItineraireService(db).remove_cooperative(itineraire_id, cooperative_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
