from datetime import date

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.api.controllers.authentication.dependencies import (
    ensure_cooperative_access,
    get_user_cooperative_ids,
    has_global_cooperative_access,
    require_permission,
)
from app.db.session import get_db
from app.models.depart import DepartStatus
from app.models.user import User
from app.schemas.common import PageResponse
from app.schemas.depart import DepartCreate, DepartRead, DepartStatusUpdate, DepartUpdate
from app.services.depart import DepartService

router = APIRouter(prefix="/departs", tags=["departs"])


def _scope(db: Session, user: User) -> set[int] | None:
    return None if has_global_cooperative_access(user) else get_user_cooperative_ids(db, user)


@router.get("", response_model=PageResponse[DepartRead])
def list_departs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None, max_length=100),
    sort_by: str = Query("date_depart", pattern="^(date_depart|heure_depart|created_at|statut)$"),
    sort_order: str = Query("asc", pattern="^(asc|desc)$"),
    statut: DepartStatus | None = None,
    id_cooperative: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    current_user: User = Depends(require_permission("DEPART_READ")),
    db: Session = Depends(get_db),
):
    if id_cooperative is not None:
        ensure_cooperative_access(db, current_user, id_cooperative)
    return DepartService(db).list_departs(
        page=page,
        page_size=page_size,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        statut=statut,
        id_cooperative=id_cooperative,
        date_from=date_from,
        date_to=date_to,
        cooperative_ids=_scope(db, current_user),
    )


@router.post("", response_model=DepartRead, status_code=status.HTTP_201_CREATED)
def create_depart(
    data: DepartCreate,
    current_user: User = Depends(require_permission("DEPART_CREATE")),
    db: Session = Depends(get_db),
):
    ensure_cooperative_access(db, current_user, data.id_cooperative)
    return DepartService(db).create_depart(**data.model_dump())


@router.get("/{depart_id}", response_model=DepartRead)
def get_depart(
    depart_id: int,
    current_user: User = Depends(require_permission("DEPART_READ")),
    db: Session = Depends(get_db),
):
    return DepartService(db).get_depart(depart_id, cooperative_ids=_scope(db, current_user))


@router.put("/{depart_id}", response_model=DepartRead)
def update_depart(
    depart_id: int,
    data: DepartUpdate,
    current_user: User = Depends(require_permission("DEPART_UPDATE")),
    db: Session = Depends(get_db),
):
    service = DepartService(db)
    current = service.get_depart(depart_id, cooperative_ids=_scope(db, current_user))
    values = data.model_dump(exclude_unset=True)
    ensure_cooperative_access(db, current_user, values.get("id_cooperative", current.id_cooperative))
    return service.update_depart(depart_id, **values)


@router.patch("/{depart_id}/status", response_model=DepartRead)
def update_depart_status(
    depart_id: int,
    data: DepartStatusUpdate,
    current_user: User = Depends(require_permission("DEPART_UPDATE")),
    db: Session = Depends(get_db),
):
    service = DepartService(db)
    service.get_depart(depart_id, cooperative_ids=_scope(db, current_user))
    return service.update_status(depart_id, data.statut)


@router.post("/{depart_id}/cancel", response_model=DepartRead)
def cancel_depart(
    depart_id: int,
    current_user: User = Depends(require_permission("DEPART_CANCEL")),
    db: Session = Depends(get_db),
):
    service = DepartService(db)
    service.get_depart(depart_id, cooperative_ids=_scope(db, current_user))
    return service.cancel_depart(depart_id)

