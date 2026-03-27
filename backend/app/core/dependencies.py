"""
Shared FastAPI dependencies — injected via Depends() in route handlers.

Available dependencies
----------------------
get_current_user      – Any authenticated user (student, instructor, or admin).
require_instructor    – Authenticated user whose role is instructor OR admin.
require_student       – Authenticated user whose role is student.
require_enrollment    – Authenticated user who is actively enrolled in the
                        course identified by the {course_id} path parameter.

Usage example
-------------
    from app.core.dependencies import get_current_user, require_instructor

    @router.get("/courses/{course_id}")
    def get_course(
        course_id: UUID,
        current_user: User = Depends(require_instructor),
        db: Session = Depends(get_db),
    ):
        ...

    @router.get("/courses/{course_id}/materials")
    def list_materials(
        course_id: UUID,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_enrollment),   # path param resolved automatically
    ):
        ...
"""
from uuid import UUID

from fastapi import Depends, HTTPException, Path, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import verify_token
from app.models.course import CourseEnrollment
from app.models.user import User

# ---------------------------------------------------------------------------
# Token extraction
# ---------------------------------------------------------------------------

# tokenUrl is the endpoint the Swagger UI "Authorize" button uses to obtain a
# token.  For Google OAuth it's not a classic username/password form, but the
# URL still tells Swagger where the auth entry-point lives.
# auto_error=False lets us return a proper 401 rather than FastAPI's default
# 422 when the header is absent.
_oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/google/login",
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
    token: str | None = Depends(_oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Extract and validate the Bearer JWT, then return the corresponding User
    row from the database.

    Raises HTTP 401 if:
      - No Authorization header is present
      - The token is expired, malformed, or has an invalid signature
      - The user_id in the token does not exist in the DB

    Raises HTTP 403 if the account has been suspended.
    """
    if not token:
        raise _CREDENTIALS_EXCEPTION

    payload = verify_token(token)
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
    """
    Allow only instructors and admins.
    Raises HTTP 403 for students.
    """
    if current_user.role not in ("instructor", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Instructor access required.",
        )
    return current_user


def require_student(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Allow only students.
    Raises HTTP 403 for instructors and admins.
    """
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
    the {course_id} path parameter.

    Admins bypass the enrollment check and are always granted access.

    Raises HTTP 403 if the user has no active enrollment in the course.
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
