"""
Shared FastAPI dependencies — injected via Depends() in route handlers.

Auth scheme: HTTPBearer
-----------------------
All protected endpoints expect:
    Authorization: Bearer <jwt>

In Swagger UI (/docs):
  1. Click the lock icon "Authorize" button (top right of the page).
  2. In the "BearerJWT" section, paste your JWT in the "Value" field.
  3. Click Authorize — every subsequent request carries the token.

To get a token during development:
  POST /api/v1/auth/dev-token  {"email": "you@domain.com", "role": "instructor"}
  Copy the access_token and paste it into the Swagger Authorize dialog.

Available dependencies
----------------------
get_current_user      – Any authenticated user (student, instructor, or admin).
require_instructor    – Authenticated user whose role is instructor OR admin.
require_student       – Authenticated user whose role is student.
require_enrollment    – Authenticated user actively enrolled in {course_id}.
"""
from uuid import UUID

from fastapi import Depends, HTTPException, Path, status, Cookie
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import verify_token
from app.models.course import CourseEnrollment
from app.models.user import User

# ---------------------------------------------------------------------------
# Token extraction
# HTTPBearer renders a clean "Value" input in Swagger (no username/password).
# ---------------------------------------------------------------------------

_bearer_scheme = HTTPBearer(
    scheme_name="BearerJWT",
    description=(
        "Paste the JWT returned by **POST /api/v1/auth/dev-token** (dev) "
        "or the Google OAuth callback (production). "
        "Do **not** prefix with 'Bearer' — just the raw token."
    ),
    auto_error=False,
)

_CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials — please log in.",
    headers={"WWW-Authenticate": "Bearer"},
)


# ---------------------------------------------------------------------------
# Core: get_current_user
# ---------------------------------------------------------------------------

def get_current_user(
    access_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
) -> User:
    """
    Extract and validate the Bearer JWT, then return the corresponding User.

    Raises HTTP 401 when the token is absent, expired, malformed, or the
    user_id does not exist in the database.
    Raises HTTP 403 when the account is suspended.
    """
    if not access_token:
        raise _CREDENTIALS_EXCEPTION


    payload = verify_token(access_token)
    if payload is None:
        raise _CREDENTIALS_EXCEPTION

    user_id: str | None = payload.get("sub")
    if not user_id:
        raise _CREDENTIALS_EXCEPTION

    user: User | None = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise _CREDENTIALS_EXCEPTION

    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been suspended. Please contact support.",
        )

    return user


# ---------------------------------------------------------------------------
# Role-gated helpers
# ---------------------------------------------------------------------------

def require_instructor(
    current_user: User = Depends(get_current_user),
) -> User:
    """Allow only instructors and admins. Raises HTTP 403 for students."""
    if current_user.role not in ("instructor", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Instructor access required.",
        )
    return current_user


def require_student(
    current_user: User = Depends(get_current_user),
) -> User:
    """Allow only students. Raises HTTP 403 for instructors and admins."""
    if current_user.role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Student access required.",
        )
    return current_user


# ---------------------------------------------------------------------------
# Enrollment check
# ---------------------------------------------------------------------------

def require_enrollment(
    course_id: UUID = Path(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    """
    Verify the current user is actively enrolled in the course given by
    the {course_id} path parameter. Admins bypass the check.
    Raises HTTP 403 if not enrolled.
    """
    if current_user.role == "admin":
        return current_user

    enrollment: CourseEnrollment | None = (
        db.query(CourseEnrollment)
        .filter(
            CourseEnrollment.course_id == course_id,
            CourseEnrollment.user_id == current_user.id,
            CourseEnrollment.is_active.is_(True),
        )
        .first()
    )

    if enrollment is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not enrolled in this course.",
        )

    return current_user
