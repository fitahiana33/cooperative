from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


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

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
