from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    first_name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    telephone: str | None = Field(default=None, max_length=30)
    address: str | None = Field(default=None, max_length=255)
    role: str = Field(default="passenger", min_length=2, max_length=100)
    password: str = Field(min_length=8, max_length=128)


class UserUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    email: EmailStr | None = None
    telephone: str | None = Field(default=None, max_length=30)
    address: str | None = Field(default=None, max_length=255)
    password: str | None = Field(default=None, min_length=8, max_length=128)
    is_active: bool | None = None


class UserRoleRead(BaseModel):
    id: int
    libelle: str

    model_config = ConfigDict(from_attributes=True)


class UserRead(BaseModel):
    id: int
    name: str
    first_name: str | None
    email: EmailStr
    telephone: str | None
    address: str | None
    role: str
    is_active: bool
    created_at: datetime
    roles: list[UserRoleRead] = []

    permissions: list[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
