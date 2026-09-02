from datetime import datetime, timedelta, timezone
import uuid

import jwt

from app.core.config import settings


def create_access_token(subject: str, role: str = "passenger") -> str:
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {
        "sub": str(subject),
        "role": role,
        "type": "access",
        "iat": int(now.timestamp()),
        "jti": str(uuid.uuid4()),
        "exp": expires_at,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(subject: str) -> str:
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=settings.refresh_token_expire_minutes)
    payload = {
        "sub": str(subject),
        "type": "refresh",
        "iat": int(now.timestamp()),
        "jti": str(uuid.uuid4()),
        "exp": expires_at,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def create_password_reset_token(email: str) -> str:
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=settings.reset_token_expire_minutes)
    payload = {
        "email": str(email),
        "type": "password_reset",
        "iat": int(now.timestamp()),
        "jti": str(uuid.uuid4()),
        "exp": expires_at,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        if payload.get("type") != "access":
            return None
        return payload
    except jwt.PyJWTError:
        return None


def decode_refresh_token(token: str) -> str | None:
    payload = decode_refresh_payload(token)
    subject = payload.get("sub") if payload else None
    return str(subject) if subject else None


def decode_refresh_payload(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        if payload.get("type") != "refresh":
            return None
        return payload
    except jwt.PyJWTError:
        return None


def decode_password_reset_token(token: str) -> str | None:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        if payload.get("type") != "password_reset":
            return None
        email = payload.get("email")
        return str(email) if email else None
    except jwt.PyJWTError:
        return None
