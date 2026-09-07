from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api.controllers.authentication.dependencies import ensure_cooperative_access, get_user_cooperative_ids, has_global_cooperative_access, require_permission, require_roles
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.common import PageResponse
from app.schemas.tarif import TarifCreate, TarifRead, TarifUpdate
from app.services.tarif import TarifService

router = APIRouter(prefix="/tarifs", tags=["tarifs"])


@router.get("", response_model=PageResponse[TarifRead])
def list_tarifs(
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None, max_length=50),
    sort_by: str = Query("date_debut", pattern="^(date_debut|prix|created_at)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    id_itineraire: int | None = None,
    current_user: User = Depends(require_permission("TARIF_READ")), db: Session = Depends(get_db),
):
    cooperative_ids = None if has_global_cooperative_access(current_user) else get_user_cooperative_ids(db, current_user)
    return TarifService(db).list_tarifs(page=page, page_size=page_size, search=search, sort_by=sort_by, sort_order=sort_order, id_itineraire=id_itineraire, cooperative_ids=cooperative_ids)


@router.post("", response_model=TarifRead, status_code=status.HTTP_201_CREATED)
def create_tarif(data: TarifCreate, current_user: User = Depends(require_permission("TARIF_CREATE")), db: Session = Depends(get_db)):
    if data.id_cooperative is not None:
        ensure_cooperative_access(db, current_user, data.id_cooperative)
    return TarifService(db).create_tarif(**data.model_dump())


@router.get("/history/{itineraire_id}", response_model=list[TarifRead])
def tarif_history(itineraire_id: int, current_user: User = Depends(require_permission("TARIF_READ")), db: Session = Depends(get_db)):
    cooperative_ids = None if has_global_cooperative_access(current_user) else get_user_cooperative_ids(db, current_user)
    return TarifService(db).history(itineraire_id, cooperative_ids=cooperative_ids)


@router.get("/{tarif_id}", response_model=TarifRead)
def get_tarif(tarif_id: int, current_user: User = Depends(require_permission("TARIF_READ")), db: Session = Depends(get_db)):
    item = TarifService(db)._get(tarif_id)
    if item.id_cooperative is not None:
        ensure_cooperative_access(db, current_user, item.id_cooperative)
    return item


@router.put("/{tarif_id}", response_model=TarifRead)
def update_tarif(tarif_id: int, data: TarifUpdate, current_user: User = Depends(require_permission("TARIF_UPDATE")), db: Session = Depends(get_db)):
    item = TarifService(db)._get(tarif_id)
    cooperative_id = data.id_cooperative if data.id_cooperative is not None else item.id_cooperative
    if cooperative_id is not None:
        ensure_cooperative_access(db, current_user, cooperative_id)
    return TarifService(db).update_tarif(tarif_id, **data.model_dump(exclude_unset=True))


@router.patch("/{tarif_id}/toggle", response_model=TarifRead)
def toggle_tarif(tarif_id: int, current_user: User = Depends(require_permission("TARIF_UPDATE")), db: Session = Depends(get_db)):
    item = TarifService(db)._get(tarif_id)
    if item.id_cooperative is not None:
        ensure_cooperative_access(db, current_user, item.id_cooperative)
    return TarifService(db).toggle_tarif(tarif_id)


@router.delete("/{tarif_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tarif(tarif_id: int, current_user: User = Depends(require_roles(UserRole.ADMIN)), db: Session = Depends(get_db)):
    item = TarifService(db)._get(tarif_id)
    if item.is_active:
        raise HTTPException(409, "Un tarif actif doit être désactivé avant sa suppression.")
    db.delete(item)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
