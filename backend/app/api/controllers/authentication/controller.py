from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Request, status
from fastapi.security import HTTPAuthorizationCredentials
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
from app.models.authentication import RevokedToken
from app.services.authentication.token import decode_access_token, decode_refresh_payload
from .dependencies import bearer, get_current_user

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


@router.post("/logout", response_model=MessageResponse)
def logout(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    user: User = Depends(get_current_user),
    data: RefreshTokenRequest | None = None,
    db: Session = Depends(get_db),
):
    access_payload = decode_access_token(credentials.credentials)
    if access_payload and access_payload.get("jti") and not db.get(RevokedToken, access_payload["jti"]):
        db.add(RevokedToken(
            jti=access_payload["jti"],
            token_type="access",
            expires_at=datetime.fromtimestamp(access_payload["exp"], tz=timezone.utc),
        ))
    if data and data.refresh_token:
        refresh_payload = decode_refresh_payload(data.refresh_token)
        if refresh_payload and refresh_payload.get("jti") and not db.get(RevokedToken, refresh_payload["jti"]):
            db.add(RevokedToken(
                jti=refresh_payload["jti"],
                token_type="refresh",
                expires_at=datetime.fromtimestamp(refresh_payload["exp"], tz=timezone.utc),
            ))
    db.commit()
    return MessageResponse(message="Déconnexion effectuée.")
