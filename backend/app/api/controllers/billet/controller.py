from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.controllers.authentication.dependencies import get_user_cooperative_ids, has_active_role, has_global_cooperative_access, require_permission
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.billet import BilletRead
from app.schemas.common import PageResponse
from app.services.billet import BilletService

router = APIRouter(prefix="/billets", tags=["billets"])


def _scope(db: Session, user: User) -> tuple[int | None, set[int] | None]:
    if has_global_cooperative_access(user):
        return None, None
    if has_active_role(user, UserRole.PASSAGER):
        return user.id, None
    return None, get_user_cooperative_ids(db, user)


@router.get("", response_model=PageResponse[BilletRead])
def list_billets(
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), search: str | None = Query(None, max_length=100),
    current_user: User = Depends(require_permission("BILLET_READ")), db: Session = Depends(get_db),
):
    owner_id, cooperative_ids = _scope(db, current_user)
    return BilletService(db).list(page=page, page_size=page_size, search=search, owner_id=owner_id, cooperative_ids=cooperative_ids)


@router.get("/{billet_id}", response_model=BilletRead)
def get_billet(
    billet_id: int,
    current_user: User = Depends(require_permission("BILLET_READ")), db: Session = Depends(get_db),
):
    owner_id, cooperative_ids = _scope(db, current_user)
    return BilletService(db).get(billet_id, owner_id=owner_id, cooperative_ids=cooperative_ids)


@router.get("/code/{code}", response_model=BilletRead)
def get_billet_by_code(
    code: str,
    current_user: User = Depends(require_permission("BILLET_READ")), db: Session = Depends(get_db),
):
    item = BilletService(db).find_by_code(code)
    owner_id, cooperative_ids = _scope(db, current_user)
    if owner_id is not None and item.reservation_place.reservation.id_user != owner_id:
        from fastapi import HTTPException
        raise HTTPException(404, "Billet introuvable.")
    if cooperative_ids is not None and item.reservation_place.reservation.depart.id_cooperative not in cooperative_ids:
        from fastapi import HTTPException
        raise HTTPException(404, "Billet introuvable.")
    return BilletService(db)._to_dict(item)

