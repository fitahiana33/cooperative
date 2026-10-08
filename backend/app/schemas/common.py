from typing import Annotated, Generic, TypeVar
from pydantic import AfterValidator, BaseModel, Field

T = TypeVar("T")

class PageResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)
    pages: int = Field(ge=0)


def _check_password_strength(value: str) -> str:
    if not any(char.isalpha() for char in value) or not any(char.isdigit() for char in value):
        raise ValueError("Le mot de passe doit contenir au moins une lettre et un chiffre.")
    return value


# Password chosen by a user: 8 to 128 characters, with letters and digits.
StrongPassword = Annotated[str, Field(min_length=8, max_length=128), AfterValidator(_check_password_strength)]
