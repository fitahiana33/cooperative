from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.schemas.role import RoleCreate, RoleUpdate, RoleRead
from app.schemas.user import UserRead
from app.schemas.permission import PermissionRead
from app.schemas.common import PageResponse
from app.services.role import RoleService
from app.api.controllers.authentication.dependencies import require_permission

router = APIRouter(prefix="/roles", tags=["roles"])

@router.get("", response_model=PageResponse[RoleRead])
def list_roles(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None, max_length=100),
    sort_by: str = Query("libelle", pattern="^(libelle|created_at)$"),
    sort_order: str = Query("asc", pattern="^(asc|desc)$"),
    _: User = Depends(require_permission("ROLE_MANAGE")),
    db: Session = Depends(get_db),
):
    return RoleService(db).list_roles(page=page, page_size=page_size, search=search, sort_by=sort_by, sort_order=sort_order)

@router.post("", response_model=RoleRead, status_code=status.HTTP_201_CREATED)
def create_role(
    data: RoleCreate,
    _: User = Depends(require_permission("ROLE_MANAGE")),
    db: Session = Depends(get_db),
):
    return RoleService(db).create_role(libelle=data.libelle, description=data.description)

@router.put("/{role_id}", response_model=RoleRead)
def update_role(
    role_id: int,
    data: RoleUpdate,
    _: User = Depends(require_permission("ROLE_MANAGE")),
    db: Session = Depends(get_db),
):
    return RoleService(db).update_role(role_id, **data.model_dump(exclude_unset=True))

@router.patch("/{role_id}/toggle", response_model=RoleRead)
def toggle_role(
    role_id: int,
    _: User = Depends(require_permission("ROLE_MANAGE")),
    db: Session = Depends(get_db),
):
    return RoleService(db).toggle_role(role_id)

@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_role(
    role_id: int,
    _: User = Depends(require_permission("ROLE_MANAGE")),
    db: Session = Depends(get_db),
):
    RoleService(db).delete_role(role_id)

@router.post("/{role_id}/permissions/{permission_id}", status_code=status.HTTP_204_NO_CONTENT)
def assign_permission(
    role_id: int,
    permission_id: int,
    _: User = Depends(require_permission("ROLE_MANAGE")),
    db: Session = Depends(get_db),
):
    RoleService(db).assign_permission_to_role(role_id, permission_id)

@router.delete("/{role_id}/permissions/{permission_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_permission(
    role_id: int,
    permission_id: int,
    _: User = Depends(require_permission("ROLE_MANAGE")),
    db: Session = Depends(get_db),
):
    RoleService(db).revoke_permission_from_role(role_id, permission_id)

@router.post("/{role_id}/users/{user_id}", response_model=UserRead)
def assign_user_role(
    role_id: int,
    user_id: int,
    _: User = Depends(require_permission("ROLE_MANAGE")),
    db: Session = Depends(get_db),
):
    return RoleService(db).assign_role_to_user(user_id, role_id)

@router.delete("/{role_id}/users/{user_id}", response_model=UserRead)
def revoke_user_role(
    role_id: int,
    user_id: int,
    _: User = Depends(require_permission("ROLE_MANAGE")),
    db: Session = Depends(get_db),
):
    return RoleService(db).revoke_role_from_user(user_id, role_id)

@router.get("/{role_id}/permissions", response_model=list[PermissionRead])
def list_role_permissions(
    role_id: int,
    _: User = Depends(require_permission("ROLE_MANAGE")),
    db: Session = Depends(get_db),
):
    return RoleService(db).get_role(role_id).permissions
