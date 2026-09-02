from datetime import datetime
from sqlalchemy import BigInteger, Boolean, DateTime, String, Table, Column, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

roles_permissions = Table(
    "roles_permissions", Base.metadata,
    Column("id_role", ForeignKey("roles.id_role", ondelete="CASCADE"), primary_key=True),
    Column("id_permission", ForeignKey("permissions.id_permission", ondelete="CASCADE"), primary_key=True),
    Column("assigned_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
)

class Role(Base):
    __tablename__ = "roles"
    id: Mapped[int] = mapped_column("id_role", BigInteger, primary_key=True)
    libelle: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    users = relationship("User", secondary="users_roles", back_populates="roles")
    permissions = relationship("Permission", secondary=roles_permissions, back_populates="roles")

class Permission(Base):
    __tablename__ = "permissions"
    id: Mapped[int] = mapped_column("id_permission", BigInteger, primary_key=True)
    libelle: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255))
    code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    module: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    roles = relationship("Role", secondary=roles_permissions, back_populates="permissions")
