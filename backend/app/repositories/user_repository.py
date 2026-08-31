from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def list(self) -> list[User]:
        return list(self.db.scalars(select(User).order_by(User.id)))

    def create(self, email: str, full_name: str) -> User:
        user = User(email=email, full_name=full_name)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

