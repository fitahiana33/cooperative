from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    first_name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    telephone: str | None = Field(default=None, max_length=30)
    address: str | None = Field(default=None, max_length=255)
    role: str = Field(default="passenger", max_length=20)
    password: str = Field(min_length=8, max_length=128)


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
    model_config = ConfigDict(from_attributes=True)
