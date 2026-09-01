from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.core.rate_limiter import limiter
from app.db.session import get_db
from app.models.user import User
from app.schemas.authentication import (
    ForgotPasswordRequest,
    LoginRequest,
    MessageResponse,
    RefreshTokenRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserRegisterRequest,
)
from app.schemas.user import UserRead
from app.services.authentication import AuthenticationService
from .dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/login", response_model=TokenResponse)
@limiter.limit("20/minute")
def login(request: Request, data: LoginRequest, db: Session = Depends(get_db)):
    return AuthenticationService(db).login(data)


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
def register(request: Request, data: UserRegisterRequest, db: Session = Depends(get_db)):
    return AuthenticationService(db).register(data)


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit("10/minute")
def refresh_token(request: Request, data: RefreshTokenRequest, db: Session = Depends(get_db)):
    return AuthenticationService(db).refresh_token(data)


@router.post("/forgot-password", response_model=MessageResponse)
@limiter.limit("10/minute")
def forgot_password(request: Request, data: ForgotPasswordRequest, db: Session = Depends(get_db)):
    return AuthenticationService(db).forgot_password(data)


@router.post("/reset-password", response_model=MessageResponse)
@limiter.limit("10/minute")
def reset_password(request: Request, data: ResetPasswordRequest, db: Session = Depends(get_db)):
    return AuthenticationService(db).reset_password(data)


@router.get("/me", response_model=UserRead)
def current_user(user: User = Depends(get_current_user)):
    return user
