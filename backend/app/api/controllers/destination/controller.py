from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.api.controllers.authentication.dependencies import require_permission, require_roles
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.common import PageResponse
from app.schemas.destination import DestinationCreate, DestinationRead, DestinationUpdate
from app.services.destination import DestinationService

router = APIRouter(prefix="/destinations", tags=["destinations"])


@router.get("", response_model=PageResponse[DestinationRead])
def list_destinations(
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None, max_length=100),
    sort_by: str = Query("nom", pattern="^(nom|region|created_at)$"),
    sort_order: str = Query("asc", pattern="^(asc|desc)$"),
    _: User = Depends(require_permission("DESTINATION_READ")), db: Session = Depends(get_db),
):
    return DestinationService(db).list_destinations(page=page, page_size=page_size, search=search, sort_by=sort_by, sort_order=sort_order)


@router.post("", response_model=DestinationRead, status_code=status.HTTP_201_CREATED)
def create_destination(data: DestinationCreate, _: User = Depends(require_roles(UserRole.ADMIN)), db: Session = Depends(get_db)):
    return DestinationService(db).create_destination(**data.model_dump())


@router.get("/{destination_id}", response_model=DestinationRead)
def get_destination(destination_id: int, _: User = Depends(require_permission("DESTINATION_READ")), db: Session = Depends(get_db)):
    return DestinationService(db).get_destination(destination_id)


@router.put("/{destination_id}", response_model=DestinationRead)
def update_destination(destination_id: int, data: DestinationUpdate, _: User = Depends(require_roles(UserRole.ADMIN)), db: Session = Depends(get_db)):
    return DestinationService(db).update_destination(destination_id, **data.model_dump(exclude_unset=True))


@router.patch("/{destination_id}/toggle", response_model=DestinationRead)
def toggle_destination(destination_id: int, _: User = Depends(require_roles(UserRole.ADMIN)), db: Session = Depends(get_db)):
    return DestinationService(db).toggle_destination(destination_id)


@router.delete("/{destination_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_destination(destination_id: int, _: User = Depends(require_roles(UserRole.ADMIN)), db: Session = Depends(get_db)):
    DestinationService(db).delete_destination(destination_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
