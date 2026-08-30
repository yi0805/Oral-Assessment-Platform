from slowapi import Limiter
from starlette.requests import Request

from app.core.config import settings

def get_trusted_client_ip(request: Request) -> str:
    """Use Nginx's sanitized forwarded client address for the loopback proxy.

    The documented deployment is browser -> local Nginx -> Gunicorn. Nginx
    overwrites X-Forwarded-For with $remote_addr, so this is the browser
    address rather than an arbitrary client-provided header. Direct local
    requests deliberately retain their local source address.
    """
    peer = request.client.host if request.client else "unknown"
    if peer in {"127.0.0.1", "::1"}:
        forwarded = request.headers.get("x-forwarded-for", "")
        client_ip = forwarded.split(",", 1)[0].strip()
        if client_ip:
            return client_ip
    return peer


# Limits are applied explicitly to costly or abuse-sensitive endpoints.
# Ordinary read APIs are intentionally not globally rate limited.

limiter = Limiter(
    key_func=get_trusted_client_ip,
)
