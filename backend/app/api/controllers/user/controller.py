from math import ceil
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import asc, desc, func, or_, select
from sqlalchemy.orm import Session

from app.api.controllers.authentication.dependencies import get_current_user, require_admin, require_permission
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserRead, UserUpdate
from app.schemas.common import PageResponse
from app.services.user import UserService
from app.services.role import RoleService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserRead)
def get_my_profile(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("", response_model=PageResponse[UserRead])
def list_users(
    _: User = Depends(require_permission("USER_READ")),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None, max_length=100),
    sort_by: str = Query("created_at", pattern="^(created_at|name|email|is_active)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
):
    statement = select(User)
    if search:
        term = f"%{search.strip()}%"
        statement = statement.where(or_(User.name.ilike(term), User.first_name.ilike(term), User.email.ilike(term)))
    column = getattr(User, sort_by)
    statement = statement.order_by((asc if sort_order == "asc" else desc)(column))
    total = db.scalar(select(func.count()).select_from(statement.subquery())) or 0
    items = list(db.scalars(statement.offset((page - 1) * page_size).limit(page_size)))
    return {"items": items, "total": total, "page": page, "page_size": page_size, "pages": ceil(total / page_size) if total else 0}


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(
    data: UserCreate,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return UserService(db).create_user(data)


@router.get("/{user_id}", response_model=UserRead)
def get_user(
    user_id: int,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    user = UserService(db).repository.find_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable.")
    return user


@router.put("/{user_id}", response_model=UserRead)
def update_user(
    user_id: int,
    data: UserUpdate,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return UserService(db).update_user(user_id, **data.model_dump(exclude_unset=True))


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    UserService(db).delete_user(user_id)


@router.patch("/{user_id}/toggle", response_model=UserRead)
def toggle_user(
    user_id: int,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable.")
    user.is_active = not user.is_active
    db.commit()
    db.refresh(user)
    return user

@router.post("/{user_id}/roles/{role_id}", response_model=UserRead)
def assign_role(
    user_id: int,
    role_id: int,
    _: User = Depends(require_permission("ROLE_MANAGE")),
    db: Session = Depends(get_db),
):
    return RoleService(db).assign_role_to_user(user_id, role_id)

@router.delete("/{user_id}/roles/{role_id}", response_model=UserRead)
def revoke_role(
    user_id: int,
    role_id: int,
    _: User = Depends(require_permission("ROLE_MANAGE")),
    db: Session = Depends(get_db),
):
    return RoleService(db).revoke_role_from_user(user_id, role_id)
