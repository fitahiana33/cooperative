from functools import lru_cache
from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


DEVELOPMENT_ENVIRONMENTS = {"development", "dev", "local", "test"}
# Values shipped in the example configuration; never acceptable outside development.
DEFAULT_SECRET_PREFIXES = ("change-me", "changeme", "change_me")
DEFAULT_ADMIN_PASSWORDS = {"Admin123!", "admin", "password"}

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
    frontend_url: str = "http://localhost:5173"
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_from: str | None = None
    smtp_use_tls: bool = True
    smtp_use_ssl: bool = False
    uploads_dir: Path = BACKEND_DIR / "uploads"
    # Periodic maintenance (reservation expiry, assignment sync, cleanup).
    scheduler_enabled: bool = True
    maintenance_interval_seconds: int = 60
    # Rate-limit counters: memory:// for one process, redis://host:6379 when scaled out.
    rate_limit_storage_uri: str = "memory://"
    # Timezone of the station; calendar dates ("today") are computed in it.
    timezone: str = "Indian/Antananarivo"
    # Returns the password-reset link in the API response. Local debugging only.
    debug_return_reset_url: bool = False
    # Minutes a reservation holds its seats before it must be paid.
    reservation_hold_minutes: int = 30
    # Limits applied to passengers booking for themselves.
    passenger_max_pending_reservations: int = 2
    passenger_max_seats_per_reservation: int = 6
    # A passenger may cancel a paid reservation until this many minutes before departure.
    cancellation_deadline_minutes: int = 120

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def is_development(self) -> bool:
        return self.environment.strip().lower() in DEVELOPMENT_ENVIRONMENTS

    @model_validator(mode="after")
    def refuse_default_secrets(self):
        if self.is_development:
            return self
        if len(self.secret_key) < 32 or self.secret_key.lower().startswith(DEFAULT_SECRET_PREFIXES):
            raise ValueError("SECRET_KEY doit être une valeur aléatoire d'au moins 32 caractères hors développement.")
        if self.default_admin_password in DEFAULT_ADMIN_PASSWORDS:
            raise ValueError("DEFAULT_ADMIN_PASSWORD ne doit pas garder sa valeur par défaut hors développement.")
        if self.jwt_algorithm not in {"HS256", "HS384", "HS512"}:
            raise ValueError("JWT_ALGORITHM doit être HS256, HS384 ou HS512.")
        if self.debug_return_reset_url:
            raise ValueError("DEBUG_RETURN_RESET_URL est réservé au développement.")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
