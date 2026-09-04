from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.schemas.permission import PermissionCreate, PermissionUpdate, PermissionRead
from app.schemas.common import PageResponse
from app.services.role import RoleService
from app.api.controllers.authentication.dependencies import require_permission

router = APIRouter(prefix="/permissions", tags=["permissions"])

@router.get("", response_model=PageResponse[PermissionRead])
def list_permissions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None, max_length=100),
    sort_by: str = Query("code", pattern="^(code|module|created_at)$"),
    sort_order: str = Query("asc", pattern="^(asc|desc)$"),
    _: User = Depends(require_permission("ROLE_MANAGE")),
    db: Session = Depends(get_db),
):
    return RoleService(db).list_permissions(page=page, page_size=page_size, search=search, sort_by=sort_by, sort_order=sort_order)

@router.post("", response_model=PermissionRead, status_code=status.HTTP_201_CREATED)
def create_permission(
    data: PermissionCreate,
    _: User = Depends(require_permission("ROLE_MANAGE")),
    db: Session = Depends(get_db),
):
    return RoleService(db).create_permission(
        code=data.code,
        libelle=data.libelle,
        module=data.module,
        description=data.description,
    )

@router.put("/{permission_id}", response_model=PermissionRead)
def update_permission(
    permission_id: int,
    data: PermissionUpdate,
    _: User = Depends(require_permission("ROLE_MANAGE")),
    db: Session = Depends(get_db),
):
    return RoleService(db).update_permission(permission_id, **data.model_dump(exclude_unset=True))

@router.delete("/{permission_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_permission(
    permission_id: int,
    _: User = Depends(require_permission("ROLE_MANAGE")),
    db: Session = Depends(get_db),
):
    RoleService(db).delete_permission(permission_id)

@router.patch("/{permission_id}/toggle", response_model=PermissionRead)
def toggle_permission(
    permission_id: int,
    _: User = Depends(require_permission("ROLE_MANAGE")),
    db: Session = Depends(get_db),
):
    permission = RoleService(db).get_permission(permission_id)
    permission.is_active = not permission.is_active
    db.commit()
    db.refresh(permission)
    return permission
