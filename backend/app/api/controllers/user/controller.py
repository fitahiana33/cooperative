from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.controllers.authentication.dependencies import get_current_user, require_admin, require_roles
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserRead
from app.services.user import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserRead)
def get_my_profile(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("", response_model=list[UserRead])
def list_users(
    _: User = Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER)),
    db: Session = Depends(get_db),
):
    return UserService(db).list_users()


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(
    data: UserCreate,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return UserService(db).create_user(data)
