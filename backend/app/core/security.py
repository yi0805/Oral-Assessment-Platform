from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt

from app.core.config import settings

def _parse_list(raw: str) -> list[str]:

    value = raw.strip().strip("[]")        
    
    return [
        item.strip().strip("\"'").lower()
        for item in value.split(",")
        if item.strip().strip("\"'")
    ]

def create_access_token(user_id: str, role: str, email: str) -> str:
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.jwt_expire_minutes)
    
    payload = {
        "id": str(user_id),
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
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )

        return payload
    
    except JWTError:
        
        return None

def resolve_role_for_new_user(email: str) -> str:

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
    
    allowed = _parse_list(settings.google_allowed_login_domains)

    email_domain = email.lower().split("@")[-1] if "@" in email else ""

    return email_domain in allowed
