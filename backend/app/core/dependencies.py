from uuid import UUID

from fastapi import Depends, HTTPException, Path, status, Cookie

from sqlalchemy.orm import Session

from app.core.database import get_db

from app.core.security import verify_token

from app.models.course import CourseEnrollment
from app.models.user import User

_CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials — please log in.",
)

def get_current_user(
    access_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
) -> User:
    if not access_token:
        raise _CREDENTIALS_EXCEPTION

    payload = verify_token(access_token)
    if payload is None:
        raise _CREDENTIALS_EXCEPTION

    user_id: str | None = payload.get("sub")
    user: User | None = db.query(User).filter(User.id == user_id).first()

    if user is None:
        raise _CREDENTIALS_EXCEPTION

    return user


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
        )
        .first()
    )

    if enrollment is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not enrolled in this course.",
        )

    return current_user
