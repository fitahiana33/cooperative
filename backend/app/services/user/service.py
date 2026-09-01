from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.user import UserCreate
from app.services.authentication.password import hash_password


class UserService:
    def __init__(self, db: Session):
        self.repository = UserRepository(db)

    def list_users(self) -> list[User]:
        return self.repository.list()

    def create_user(self, data: UserCreate) -> User:
        user = User(
            name=data.name,
            first_name=data.first_name,
            email=str(data.email),
            telephone=data.telephone,
            address=data.address,
            password_hash=hash_password(data.password),
        )
        return self.repository.create(user)
