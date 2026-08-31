from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.user import UserCreate, UserRead
from app.services.user_service import UserService

api_router = APIRouter()


@api_router.get("/users", response_model=list[UserRead], tags=["users"])
def list_users(db: Session = Depends(get_db)):
    return UserService(db).list_users()


@api_router.post("/users", response_model=UserRead, status_code=status.HTTP_201_CREATED, tags=["users"])
def create_user(data: UserCreate, db: Session = Depends(get_db)):
    return UserService(db).create_user(data)

