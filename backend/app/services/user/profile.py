"""Authenticated profile photos, validated and re-encoded before private storage."""
import io
import logging
import re
import warnings
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException
from PIL import Image, ImageOps, UnidentifiedImageError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.user import User

logger = logging.getLogger("cooperative.profile")
MAX_PHOTO_BYTES = 4 * 1024 * 1024
MAX_PHOTO_PIXELS = 10_000_000


def photo_path(version: str | None) -> Path:
    if not version or not re.fullmatch(r"[a-f0-9]{32}", version):
        raise HTTPException(status_code=404, detail="Aucune photo de profil.")
    return settings.uploads_dir / "profiles" / f"{version}.jpg"


def remove_photo_file(version: str | None) -> None:
    if not version:
        return
    try:
        photo_path(version).unlink(missing_ok=True)
    except (OSError, HTTPException):
        logger.warning("Impossible de nettoyer une ancienne photo de profil.")


def normalize_photo(content: bytes) -> bytes:
    if len(content) > MAX_PHOTO_BYTES:
        raise HTTPException(status_code=413, detail="La photo doit faire au maximum 4 Mo.")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(content)) as source:
                if source.format not in {"JPEG", "PNG", "WEBP"}:
                    raise ValueError("format")
                if source.width * source.height > MAX_PHOTO_PIXELS:
                    raise ValueError("dimensions")
                source.load()
                image = ImageOps.exif_transpose(source).convert("RGBA")
                image.thumbnail((512, 512), Image.Resampling.LANCZOS)
                # Flatten transparency and discard EXIF/GPS and other metadata.
                clean = Image.new("RGB", image.size, "white")
                clean.paste(image, mask=image.getchannel("A"))
                output = io.BytesIO()
                clean.save(output, format="JPEG", quality=88, optimize=True)
                return output.getvalue()
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise HTTPException(status_code=400, detail="Photo invalide. Choisissez une image JPEG, PNG ou WebP de 10 millions de pixels maximum.")


def replace_photo(db: Session, user_id: int, content: bytes | None) -> User:
    # Decode before taking the lock; competing changes serialize on the account.
    normalized = normalize_photo(content) if content is not None else None
    user = db.scalar(select(User).where(User.id == user_id).with_for_update().execution_options(populate_existing=True))
    if user is None:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable.")
    previous = user.photo_version
    version = uuid4().hex if normalized is not None else None
    try:
        if version:
            destination = photo_path(version)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(normalized)
        user.photo_version = version
        db.commit()
    except Exception:
        db.rollback()
        remove_photo_file(version)
        raise
    remove_photo_file(previous)
    db.refresh(user)
    return user
