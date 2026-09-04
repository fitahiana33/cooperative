import logging
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.models.role import Role
from app.models.authentication import RevokedToken
from datetime import datetime, timezone
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
    decode_password_reset_payload,
    decode_refresh_payload,
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

        user.last_login_at = datetime.now(timezone.utc)
        self.db.commit()
        access_token = create_access_token(subject=str(user.id), role=user.role)
        refresh_token = create_refresh_token(subject=str(user.id))

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user=UserRead.model_validate(user),
        )

    def register(self, data: UserRegisterRequest) -> TokenResponse:
        name = data.name.strip()
        first_name = data.first_name.strip()
        if not name or not first_name:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Le nom et le prénom sont obligatoires.",
            )

        email_clean = str(data.email).lower().strip()
        existing = self.users.find_by_email(email_clean)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cet adresse email est déjà utilisée.",
            )

        passenger_role = self.db.query(Role).filter(Role.libelle == UserRole.PASSAGER).first()
        if not passenger_role or not passenger_role.is_active:
            logger.error("Rôle passager absent ou inactif lors de l'inscription")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Le service d'inscription n'est pas correctement configuré.",
            )

        new_user = User(
            name=name,
            first_name=first_name,
            email=email_clean,
            telephone=data.telephone.strip() if data.telephone else None,
            address=data.address.strip() if data.address else None,
            password_hash=hash_password(data.password),
            is_active=True,
        )

        new_user.roles.append(passenger_role)
        try:
            self.db.add(new_user)
            self.db.commit()
            self.db.refresh(new_user)
            user = new_user
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Impossible de créer ce compte avec les informations fournies.",
            )
        except Exception:
            self.db.rollback()
            logger.exception("Erreur interne lors de l'inscription email=%s", email_clean)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Une erreur est survenue lors de la création du compte.",
            )
        access_token = create_access_token(subject=str(user.id), role=user.role)
        refresh_token = create_refresh_token(subject=str(user.id))

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user=UserRead.model_validate(user),
        )

    def refresh_token(self, data: RefreshTokenRequest) -> TokenResponse:
        refresh_payload = decode_refresh_payload(data.refresh_token)
        refresh_jti = refresh_payload.get("jti") if refresh_payload else None
        if refresh_payload and (not refresh_jti or self.db.get(RevokedToken, refresh_jti)):
            refresh_payload = None
        user_id_str = str(refresh_payload.get("sub")) if refresh_payload and refresh_payload.get("sub") is not None else None
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

        # Rotation : dès qu'un refresh token est utilisé, il ne peut plus être
        # rejoué. La révocation est persistée dans PostgreSQL.
        try:
            self.db.add(RevokedToken(
                jti=refresh_jti,
                token_type="refresh",
                expires_at=datetime.fromtimestamp(refresh_payload["exp"], tz=timezone.utc),
            ))
            self.db.commit()
        except (KeyError, TypeError, ValueError, IntegrityError):
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token de rafraîchissement invalide ou déjà utilisé.",
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
            create_password_reset_token(email_clean)
            # In a production environment, send an email with the reset token / link.
            logger.info(
                "[PASSWORD_RESET] Reset token generated for email=%s at=%s",
                email_clean,
                datetime.now(timezone.utc).isoformat(),
            )

        return MessageResponse(
            message="Si cet email existe dans notre système, des instructions de réinitialisation ont été envoyées."
        )

    def reset_password(self, data: ResetPasswordRequest) -> MessageResponse:
        payload = decode_password_reset_payload(data.token)
        if not payload or self.db.get(RevokedToken, payload.get("jti")):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token de réinitialisation invalide ou expiré.",
            )

        email = str(payload["email"]).lower().strip()

        user = self.users.find_by_email(email)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Utilisateur non trouvé.",
            )

        user.password_hash = hash_password(data.new_password)
        try:
            self.db.add(RevokedToken(
                jti=payload["jti"],
                token_type="password_reset",
                expires_at=datetime.fromtimestamp(payload["exp"], tz=timezone.utc),
            ))
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token de réinitialisation invalide ou déjà utilisé.",
            )

        return MessageResponse(message="Votre mot de passe a été réinitialisé avec succès.")
