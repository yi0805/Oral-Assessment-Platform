"""
Authentication & authorization utilities.

Handles: JWT token creation/validation.

The Google OAuth network calls (code exchange, userinfo fetch) live in
app/api/routes/auth.py so that FastAPI can inject the DB session and return
proper HTTP errors.  This module stays pure-utility — no I/O.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt

from app.core.config import settings


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------

def create_access_token(user_id: str, role: str, email: str) -> str:
    """
    Encode a signed JWT containing the caller's identity.

    Claims included:
      sub   – user UUID (primary key in the users table)
      role  – "student" | "instructor" | "admin"
      email – used only for display; do not rely on it for authz decisions
      iat   – issued-at (UTC)
      exp   – expiry  (UTC, settings.jwt_expire_minutes from now)
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {
        "sub": str(user_id),
        "role": role,
        "email": email,
        "iat": now,
        "exp": expire,
    }
    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def verify_token(token: str) -> Optional[dict]:
    """
    Decode and validate a JWT.

    Returns the payload dict on success, or None if the token is invalid,
    expired, or tampered with.  Callers are responsible for raising an
    appropriate HTTP error.
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        return payload
    except JWTError:
        return None


# ---------------------------------------------------------------------------
# Helpers for parsing domain/email list env vars
# ---------------------------------------------------------------------------

def _parse_list(raw: str) -> list[str]:
    """
    Parse a comma-separated or JSON-array-style environment variable value
    into a clean list of lowercase, stripped strings.

    Handles both formats used in the project .env:
        auckland.ac.nz
        [aucklanduni.ac.nz,auckland.ac.nz]
        ["aucklanduni.ac.nz", "auckland.ac.nz"]
    """
    value = raw.strip().strip("[]")          # remove optional [ ] brackets
    return [
        item.strip().strip("\"'").lower()
        for item in value.split(",")
        if item.strip().strip("\"'")
    ]


# ---------------------------------------------------------------------------
# Role-assignment helper (used only during new-user creation in the callback)
# ---------------------------------------------------------------------------

def resolve_role_for_new_user(email: str) -> str:
    """
    Determine the system role to assign when a brand-new Google account signs
    in for the first time.

    Priority order
    --------------
    1. Email is in GOOGLE_INSTRUCTOR_ALLOWLIST  → instructor
    2. Email domain is in GOOGLE_INSTRUCTOR_DOMAINS → instructor
    3. Anything else → student

    Env-var names (all in .env):
        GOOGLE_INSTRUCTOR_ALLOWLIST=alice@gmail.com,teacher@auckland.ac.nz
        GOOGLE_INSTRUCTOR_DOMAINS=auckland.ac.nz
        GOOGLE_STUDENT_DOMAINS=aucklanduni.ac.nz   (informational; unused here)
    """
    allowlist = _parse_list(settings.google_instructor_allowlist)
    instructor_domains = _parse_list(settings.google_instructor_domains)

    email_lower = email.lower()
    email_domain = email_lower.split("@")[-1] if "@" in email_lower else ""

    if email_lower in allowlist:
        return "instructor"
    if email_domain and email_domain in instructor_domains:
        return "instructor"
    return "student"


def is_login_domain_allowed(email: str) -> bool:
    """
    Return True if the user is permitted to log in at all.

    When GOOGLE_ALLOWED_LOGIN_DOMAINS is non-empty, only email addresses
    whose domain appears in that list are allowed.  An empty / blank value
    means any Google account may log in.
    """
    allowed = _parse_list(settings.google_allowed_login_domains)
    if not allowed:
        return True  # no restriction configured

    email_domain = email.lower().split("@")[-1] if "@" in email else ""
    return email_domain in allowed
