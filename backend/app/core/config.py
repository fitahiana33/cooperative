from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = BACKEND_DIR / ".env"
if not ENV_FILE.exists():
    ENV_FILE = BACKEND_DIR.parent / ".env"


class Settings(BaseSettings):
    app_name: str
    environment: str
    database_url: str
    secret_key: str
    api_v1_prefix: str
    allowed_origins: list[str]
    jwt_algorithm: str
    access_token_expire_minutes: int = 60
    refresh_token_expire_minutes: int = 10080  # 7 days
    reset_token_expire_minutes: int = 30       # 30 minutes
    default_admin_email: str
    default_admin_password: str

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
