"""
WebSocket authentication helpers for streaming routes.

FastAPI's HTTP dependency injection (``Depends(require_student)``)
doesn't apply to WebSocket handshakes — the auth has to be performed
manually inside the route, before ``websocket.accept()`` is called.
This module provides the WebSocket equivalents of
``app.core.dependencies.get_current_user`` and ``require_student`` so
the upcoming ``/sessions/{id}/transcribe/stream`` route (issue #72)
can validate the connection without duplicating the JWT parsing logic.

Token discovery
---------------
Two carriers are supported, in order of preference:

1. The ``access_token`` cookie. This is the same cookie the HTTP
   routes already use, and browsers attach it automatically on
   same-origin WebSocket handshakes — no client changes required.
2. The ``?token=...`` query parameter. Fallback for tooling
   (curl-style WebSocket clients, browser DevTools experimentation)
   that can't easily set cookies.

The ``Sec-WebSocket-Protocol`` subprotocol approach is intentionally
not implemented yet: it requires the server to echo back exactly one
of the offered protocols when accepting, which adds plumbing the
current callers don't need. Add it here if a non-browser client ever
needs it.

Failure semantics
-----------------
On any auth failure the helpers close the WebSocket with code 1008
(policy violation, RFC 6455) and raise :class:`WebSocketDisconnect`.
The caller must treat the exception as "return immediately, do not
try to send anything else" — the connection is gone.
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.core.security import verify_token
from app.models import User

logger = logging.getLogger(__name__)

# WS close code 1008 is "policy violation" per RFC 6455 — the standard
# choice for refusing a connection on auth grounds. We use it for every
# failure mode so the client only has to handle one rejection code.
_WS_POLICY_VIOLATION = 1008


def _extract_token(websocket: WebSocket) -> Optional[str]:
    """Return the access token from the handshake, or ``None`` if absent."""
    cookie_token = websocket.cookies.get("access_token")
    if cookie_token:
        return cookie_token

    query_token = websocket.query_params.get("token")
    if query_token:
        return query_token

    return None


async def _reject(websocket: WebSocket, *, reason: str) -> None:
    """
    Close the WebSocket with a uniform policy-violation code and a
    human-readable reason. Centralised so we never accidentally vary
    the close code between failure paths.
    """
    logger.info("[WS auth] rejected: %s", reason)
    try:
        await websocket.close(code=_WS_POLICY_VIOLATION, reason=reason)
    except Exception:  # noqa: BLE001
        # The client may already have gone away. Closing a
        # not-fully-open WebSocket can raise; don't let it mask the
        # real auth failure that's about to be raised by the caller.
        logger.debug("[WS auth] close() raised on rejection", exc_info=True)


async def authenticate_ws(
    websocket: WebSocket,
    db: Session,
) -> User:
    """
    Validate the WebSocket handshake and return the authenticated user.

    Mirrors :func:`app.core.dependencies.get_current_user` for the
    WebSocket protocol. Closes the connection (code 1008) and raises
    :class:`WebSocketDisconnect` on any failure — missing token,
    bad signature, expired token, or user not found.

    The WebSocket is *not* accepted on success; the caller must call
    ``await websocket.accept()`` afterwards.
    """
    token = _extract_token(websocket)
    if not token:
        await _reject(websocket, reason="missing access token")
        raise WebSocketDisconnect(code=_WS_POLICY_VIOLATION)

    payload = verify_token(token)
    if payload is None:
        await _reject(websocket, reason="invalid or expired token")
        raise WebSocketDisconnect(code=_WS_POLICY_VIOLATION)

    user_id = payload.get("id")
    if not user_id:
        await _reject(websocket, reason="malformed token payload")
        raise WebSocketDisconnect(code=_WS_POLICY_VIOLATION)

    user: Optional[User] = (
        db.query(User).filter(User.id == user_id).first()
    )
    if user is None:
        await _reject(websocket, reason="user not found")
        raise WebSocketDisconnect(code=_WS_POLICY_VIOLATION)

    return user


async def authenticate_ws_student(
    websocket: WebSocket,
    db: Session,
) -> User:
    """
    Same as :func:`authenticate_ws` but additionally requires the
    user's role to be ``"student"``. Mirrors
    :func:`app.core.dependencies.require_student` for WebSockets.

    Used by the streaming-transcription route — instructors and other
    roles must not be able to open a student-only stream.
    """
    user = await authenticate_ws(websocket, db)

    if user.role != "student":
        await _reject(websocket, reason="student role required")
        raise WebSocketDisconnect(code=_WS_POLICY_VIOLATION)

    return user
