def normalize_role(value: str) -> str:
    """Return the canonical role representation used by the application."""
    return value.strip().lower()
