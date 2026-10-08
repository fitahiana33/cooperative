from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings

# Behind a proxy (Render, nginx) the client address comes from X-Forwarded-For,
# which uvicorn only trusts with --proxy-headers --forwarded-allow-ips.
# Use a shared storage (redis://...) when the API runs several processes.
limiter = Limiter(key_func=get_remote_address, storage_uri=settings.rate_limit_storage_uri)
