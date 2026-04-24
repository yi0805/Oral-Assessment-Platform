import httpx

from fastapi import APIRouter, Depends, HTTPException, status, Header, Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.security import create_access_token, is_login_domain_allowed, resolve_role_for_new_user

from app.models import User, CourseEnrollment
from app.schemas import GoogleLoginResponse, UserResponse

router = APIRouter()

_GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"


# Helpers

def _fetch_google_userinfo(token: str) -> dict:
    resp = httpx.get(
        _GOOGLE_USERINFO_URL,
        headers={"Authorization": f"Bearer {token}"},
        timeout=10.0,
    )

    if resp.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Google userinfo fetch failed: {resp.text}",
        )

    return resp.json()


def _upsert_user(db: Session, email: str, full_name: str, upi: str, image: str | None) -> User:
    user: User | None = db.query(User).filter(User.email == email).first()

    if user:       
        return user

    role = resolve_role_for_new_user(email)

    user = User(
        email=email,
        full_name=full_name,
        upi=upi,
        role=role,
        image=image,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


# Login

@router.post(
    "/google/login",
    response_model=GoogleLoginResponse,
    summary="Login or sign up a new user if not existing",
)
def login_with_google(
    response: Response,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid Authorization header")

    token = authorization[len("Bearer "):]

    userinfo = _fetch_google_userinfo(token)

    email = userinfo.get("email")
    full_name = userinfo.get("name")
    image = userinfo.get("picture")

    if not email or not full_name:
        raise HTTPException(status_code=400, detail="Missing required Google user info")

    # Fetch upi from student email
    upi = email.split("@")[0]

    if not upi:
        raise HTTPException(status_code=400, detail="Invalid UPI format.")

    if not is_login_domain_allowed(email):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your email domain is not permitted to access this application.",
        )

    user = _upsert_user(db, email=email, full_name=full_name, upi=upi, image=image)

    # Link any existing enrollments (imported via CSV)
    db.query(CourseEnrollment).filter(
        CourseEnrollment.upi == upi,
        CourseEnrollment.user_id == None,
    ).update({"user_id": user.id})
    db.commit()

    jwt_token = create_access_token(
        user_id=str(user.id),
        role=user.role,
        email=user.email,
    )

    response.set_cookie(
        key="access_token",
        value=jwt_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=60 * 60 * 3,
        path="/",
    )

    return GoogleLoginResponse(user=user)


# Logout

@router.post(
    "/google/logout",
    summary="user Logout",
)
def logout(response: Response):
    response.delete_cookie(
        key="access_token",
        httponly=True,
        secure=False,
        samesite="lax",
        path="/",
    )

    return {"message": "Logged out successfully."}


# Current user

@router.get(
    "/google/me",
    response_model=UserResponse,
    summary="Frontend can call this to get the current logged-in user's info, or 401 if not authenticated.",
)
def get_user_info(
    current_user: User = Depends(get_current_user),
):
    return current_user