"""
Shared slowapi rate-limiter instance.

Defined here (not in app.main) to avoid circular imports:
  app.main → app.api.router → app.api.routes.auth → app.main  ✗ (circular)
  app.main → app.core.limiter                                  ✓
  app.api.routes.* → app.core.limiter                          ✓
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{settings.rate_limit_default}/minute"],
)
