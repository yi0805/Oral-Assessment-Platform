from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings

# prevent excessive API call for example hacking or abuse

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{settings.rate_limit_default}/minute"],
)
