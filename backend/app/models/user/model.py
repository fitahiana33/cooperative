from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Table, Column, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class UserRole:
    ADMIN = "admin"
    RESPONSABLE_GARE = "responsable_gare"
    AGENT_GARE = "agent_gare"
    RESPONSABLE_COOPERATIVE = "responsable_cooperative"
    CHAUFFEUR = "chauffeur"
    PASSAGER = "passenger"
    # Backward-compatible aliases used by the existing UI.
    MANAGER = RESPONSABLE_GARE
    DRIVER = CHAUFFEUR
    PASSENGER = PASSAGER


users_roles = Table(
    "users_roles", Base.metadata,
    Column("id_user", ForeignKey("users.id_user", ondelete="CASCADE"), primary_key=True),
    Column("id_role", ForeignKey("roles.id_role", ondelete="CASCADE"), primary_key=True),
    Column("assigned_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column("id_user", BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    first_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    email: Mapped[str] = mapped_column(String(150), unique=True, index=True, nullable=False)
    telephone: Mapped[str | None] = mapped_column(String(30))
    address: Mapped[str | None] = mapped_column("adresse", String(255))
    password_hash: Mapped[str] = mapped_column("password", String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    roles = relationship("Role", secondary=users_roles, back_populates="users")
    cooperatives = relationship("CooperativeMember", back_populates="user")

    @property
    def role(self) -> str:
        active_roles = [role.libelle for role in self.roles if role.is_active]
        return active_roles[0] if active_roles else UserRole.PASSENGER
