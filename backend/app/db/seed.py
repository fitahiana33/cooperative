from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.user import User, UserRole
from app.repositories.user import UserRepository
from app.services.authentication.password import hash_password


def seed_default_admin(db: Session) -> None:
    repository = UserRepository(db)
    if repository.find_by_email(settings.default_admin_email):
        return
    repository.create(User(
        name="Admin",
        first_name="Système",
        email=settings.default_admin_email,
        password_hash=hash_password(settings.default_admin_password),
        role=UserRole.ADMIN,
        is_active=True,
    ))
