import logging
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.repositories.user import UserRepository
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
from .password import hash_password, verify_password
from .token import (
    create_access_token,
    create_password_reset_token,
    create_refresh_token,
    decode_password_reset_token,
    decode_refresh_token,
)

logger = logging.getLogger("cooperative.auth")


class AuthenticationService:
    def __init__(self, db: Session):
        self.db = db
        self.users = UserRepository(db)

    def login(self, data: LoginRequest) -> TokenResponse:
        user = self.users.find_by_email(str(data.email).lower().strip())
        if not user or not user.is_active or not verify_password(data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email ou mot de passe incorrect.",
            )

        access_token = create_access_token(subject=str(user.id), role=user.role)
        refresh_token = create_refresh_token(subject=str(user.id))

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user=UserRead.model_validate(user),
        )

    def register(self, data: UserRegisterRequest) -> TokenResponse:
        email_clean = str(data.email).lower().strip()
        existing = self.users.find_by_email(email_clean)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cet adresse email est déjà utilisée.",
            )

        new_user = User(
            name=data.name.strip(),
            first_name=data.first_name.strip(),
            email=email_clean,
            telephone=data.telephone.strip() if data.telephone else None,
            address=data.address.strip() if data.address else None,
            password_hash=hash_password(data.password),
            role=UserRole.PASSENGER,
            is_active=True,
        )

        user = self.users.create(new_user)
        access_token = create_access_token(subject=str(user.id), role=user.role)
        refresh_token = create_refresh_token(subject=str(user.id))

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user=UserRead.model_validate(user),
        )

    def refresh_token(self, data: RefreshTokenRequest) -> TokenResponse:
        user_id_str = decode_refresh_token(data.refresh_token)
        if not user_id_str or not user_id_str.isdigit():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token de rafraîchissement invalide ou expiré.",
            )

        user = self.users.find_by_id(int(user_id_str))
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Utilisateur introuvable ou inactif.",
            )

        new_access_token = create_access_token(subject=str(user.id), role=user.role)
        new_refresh_token = create_refresh_token(subject=str(user.id))

        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            user=UserRead.model_validate(user),
        )

    def forgot_password(self, data: ForgotPasswordRequest) -> MessageResponse:
        email_clean = str(data.email).lower().strip()
        user = self.users.find_by_email(email_clean)
        if user and user.is_active:
            reset_token = create_password_reset_token(email_clean)
            # In a production environment, send an email with the reset token / link.
            logger.info(f"[PASSWORD_RESET] Token generated for {email_clean}: {reset_token}")

        return MessageResponse(
            message="Si cet email existe dans notre système, des instructions de réinitialisation ont été envoyées."
        )

    def reset_password(self, data: ResetPasswordRequest) -> MessageResponse:
        email = decode_password_reset_token(data.token)
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token de réinitialisation invalide ou expiré.",
            )

        user = self.users.find_by_email(email)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Utilisateur non trouvé.",
            )

        user.password_hash = hash_password(data.new_password)
        self.users.update(user)

        return MessageResponse(message="Votre mot de passe a été réinitialisé avec succès.")
