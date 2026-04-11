from fastapi import Depends, HTTPException, status, Cookie
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import verify_token

from app.models import User

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


    if current_user.role != "instructor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Instructor access required.",
        )
    
    return current_user


def require_student(
    current_user: User = Depends(get_current_user),
) -> User:
    
    if current_user.role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Student access required.",
        )
    
    return current_user
