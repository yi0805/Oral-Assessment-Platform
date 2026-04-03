"""
Auth routes: Google OAuth 2.0 login, callback, user profile, logout.

Flow
----
1. Frontend sends the user to  GET /auth/google/login
2. Backend redirects to Google's consent screen (with a signed state cookie
   to prevent CSRF).
3. Google redirects back to  GET /auth/google/callback?code=…&state=…
4. Backend:
      a. Verifies the state cookie.
      b. Exchanges the authorization code for an access token.
      c. Fetches the user's profile from Google's userinfo endpoint.
      d. Creates or updates the user row in the database.
      e. Issues a signed JWT.
      f. Redirects to  {FRONTEND_URL}/auth/callback?token=<jwt>&role=<role>
         (If FRONTEND_URL is empty, returns JSON instead for API testing.)
5. Frontend stores the JWT and routes the user to the student or instructor
   dashboard based on the `role` field.

Role assignment for NEW accounts
---------------------------------
  1. Email is in INSTRUCTOR_EMAIL_WHITELIST → instructor
  2. Email domain is in INSTRUCTOR_EMAIL_DOMAINS → instructor
  3. Anything else → student
Existing accounts keep whatever role is already stored in the database.

CSRF protection
---------------
A random 32-byte hex state token is generated in /google/login, set as an
HttpOnly SameSite=Lax cookie named `oauth_state`, and verified against the
`state` query-param that Google sends back to /google/callback.  The cookie
is deleted after verification regardless of success or failure.
"""
import secrets
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, status, Header, Response
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.limiter import limiter
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.security import create_access_token, is_login_domain_allowed, resolve_role_for_new_user
from app.models.user import User
from app.schemas.user import UserOut

router = APIRouter()


# ---------------------------------------------------------------------------
# Dev-only token endpoint (DEBUG=true only — never available in production)
# ---------------------------------------------------------------------------

class _DevTokenRequest(BaseModel):
    email: str
    role: str | None = None   # auto-resolved if omitted


class _DevTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    user: dict


@router.post(
    "/dev-token",
    response_model=_DevTokenResponse,
    summary="[DEV ONLY] Issue a JWT directly",
    description=(
        "**Available only when DEBUG=true.** "
        "Creates or upserts a user by email, assigns the role you specify "
        "(or auto-resolves it from env-var rules), and returns a signed JWT. "
        "Use this to bypass the Google OAuth flow during local development and testing. "
        "This endpoint is automatically disabled when DEBUG=false."
    ),
)
@limiter.limit(f"{settings.rate_limit_auth}/minute")
def dev_token(
    request: Request,
    payload: _DevTokenRequest,
    db: Session = Depends(get_db),
):
    if not settings.debug:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not found.",   # deliberately opaque in production
        )

    email = payload.email.strip().lower()
    if not email or "@" not in email:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="A valid email address is required.",
        )

    # Resolve role: explicit override → env-var rules → student
    if payload.role and payload.role in ("student", "instructor", "admin"):
        role = payload.role
    else:
        role = resolve_role_for_new_user(email)

    # Upsert user (no google_sub in dev mode — use email as unique key)
    user = db.query(User).filter(User.email == email).first()
    if user:
        # Update role if explicitly supplied, otherwise keep existing role
        if payload.role and payload.role in ("student", "instructor", "admin"):
            user.role = role
        else:
            role = user.role    # keep existing role
        db.commit()
        db.refresh(user)
    else:
        user = User(
            google_sub=f"dev-{email}",    # placeholder sub for dev accounts
            email=email,
            full_name=email.split("@")[0].replace(".", " ").title(),
            role=role,
            status="active",
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    token = create_access_token(
        user_id=str(user.id),
        role=user.role,
        email=user.email,
    )

    return _DevTokenResponse(
        access_token=token,
        role=user.role,
        user={
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
        },
    )


# ---------------------------------------------------------------------------
# Google OAuth constants
# ---------------------------------------------------------------------------

_GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
_GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
_GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"
_OAUTH_STATE_COOKIE = "oauth_state"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_google_auth_url(state: str) -> str:
    """Return the Google consent-screen URL for this request."""
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "online",
        "prompt": "select_account",   # always show the account picker
    }
    return f"{_GOOGLE_AUTH_URL}?{urlencode(params)}"


def _exchange_code_for_token(code: str) -> dict:
    """
    POST to Google's token endpoint and return the parsed JSON response.
    Raises HTTP 502 if Google returns an error.
    """
    resp = httpx.post(
        _GOOGLE_TOKEN_URL,
        data={
            "code": code,
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "redirect_uri": settings.google_redirect_uri,
            "grant_type": "authorization_code",
        },
        timeout=10.0,
    )
    if resp.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Google token exchange failed: {resp.text}",
        )
    return resp.json()


def _fetch_google_userinfo(access_token: str) -> dict:
    """
    Call Google's userinfo endpoint and return the parsed JSON.
    Raises HTTP 502 on failure.

    Expected fields: sub, email, email_verified, name, picture,
                     given_name, family_name.
    """
    resp = httpx.get(
        _GOOGLE_USERINFO_URL,
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=10.0,
    )
    if resp.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Google userinfo fetch failed: {resp.text}",
        )
    return resp.json()


def _upsert_user(db: Session, google_sub: str, email: str, full_name: str, image: str | None) -> User:
    """
    Find an existing user by google_sub (preferred) or email, or create a
    new one.

    - If found by google_sub: update name in case it changed; keep role.
    - If found by email only: attach the google_sub; keep role & name.
    - If brand new: assign role via resolve_role_for_new_user().
    """
    #  developing only: change role between instructor and student by setting GOOGLE_INSTRUCTOR_ALLOWLIST in .env to your email or leave it empty to default to student
    role = resolve_role_for_new_user(email)


    # 1. Look up by Google subject ID (most reliable — survives email changes)
    user: User | None = db.query(User).filter(User.google_sub == google_sub).first()

    if user:
        # Keep the existing role — only refresh the display name.
        user.full_name = full_name
        user.image = image
        user.role = role
        db.commit()
        db.refresh(user)
        return user

    # 2. Look up by email (handles accounts created before OAuth was wired up)
    user = db.query(User).filter(User.email == email).first()
    if user:
        user.google_sub = google_sub
        user.full_name = full_name
        user.image = image
        user.role = role
        db.commit()
        db.refresh(user)
        return user

    # 3. Brand-new account → assign role based on email heuristics
    role = resolve_role_for_new_user(email)
    user = User(
        google_sub=google_sub,
        email=email,
        full_name=full_name,
        role=role,
        status="active",
        image=image,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ---------------------------------------------------------------------------
# Route: redirect to Google
# ---------------------------------------------------------------------------

# @router.get(
#     "/google/login",
#     summary="Initiate Google OAuth 2.0 login",
#     description=(
#         "Redirects the browser to Google's consent screen. "
#         "Sets an HttpOnly `oauth_state` cookie to prevent CSRF attacks."
#     ),
# )
# def google_login():
#     if not settings.google_client_id or not settings.google_client_secret:
#         raise HTTPException(
#             status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
#             detail=(
#                 "Google OAuth is not configured. "
#                 "Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in the environment."
#             ),
#         )

#     state = secrets.token_hex(32)
#     auth_url = _build_google_auth_url(state)

#     response = RedirectResponse(url=auth_url, status_code=302)
#     response.set_cookie(
#         key=_OAUTH_STATE_COOKIE,
#         value=state,
#         httponly=True,
#         samesite="lax",
#         max_age=600,          # 10 minutes — more than enough to complete the flow
#         secure=not settings.debug,  # HTTPS-only in production
#     )
#     return response


# ---------------------------------------------------------------------------
# Route: OAuth callback
# ---------------------------------------------------------------------------

@router.get(
    "/google/callback",
    summary="Google OAuth 2.0 callback",
    description=(
        "Handles the redirect from Google. Exchanges the authorization code "
        "for user info, upserts the user in the database, issues a JWT, and "
        "redirects to the frontend."
    ),
)
def google_callback(
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    oauth_state: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
):
    # ------------------------------------------------------------------
    # Always clear the state cookie, success or failure.
    # ------------------------------------------------------------------
    def _clear_state_cookie(response):
        response.delete_cookie(_OAUTH_STATE_COOKIE)
        return response

    # ------------------------------------------------------------------
    # 1. Handle user-denied consent
    # ------------------------------------------------------------------
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Google OAuth error: {error}",
        )

    # ------------------------------------------------------------------
    # 2. Require both code and state
    # ------------------------------------------------------------------
    if not code or not state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing 'code' or 'state' query parameter.",
        )

    # ------------------------------------------------------------------
    # 3. CSRF check — state must match the cookie we set in /google/login.
    #    In DEBUG mode the check is relaxed: we only verify that a state
    #    value was provided (we skip the cookie comparison).  This avoids
    #    localhost 127.0.0.1 ↔ localhost cookie-domain mismatch issues
    #    that are harmless in a dev environment.
    #    In production (DEBUG=false) the full cookie comparison is enforced.
    # ------------------------------------------------------------------
    if settings.debug:
        # Dev: just confirm that Google sent a non-empty state back.
        if not state:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing state parameter from Google.",
            )
    else:
        if not oauth_state or not secrets.compare_digest(state, oauth_state):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid OAuth state — possible CSRF attempt. Please try logging in again.",
            )

    # ------------------------------------------------------------------
    # 4. Exchange the authorization code for tokens
    # ------------------------------------------------------------------
    token_data = _exchange_code_for_token(code)
    access_token = token_data.get("access_token")
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Google did not return an access token.",
        )

    # ------------------------------------------------------------------
    # 5. Fetch user profile from Google
    # ------------------------------------------------------------------
    userinfo = _fetch_google_userinfo(access_token)

    google_sub: str | None = userinfo.get("sub")
    email: str | None = userinfo.get("email")
    full_name: str = userinfo.get("name") or userinfo.get("email", "Unknown")
    email_verified: bool = userinfo.get("email_verified", False)

    if not google_sub or not email:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Google userinfo response is missing required fields (sub, email).",
        )

    if not email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your Google account email is not verified. Please verify it and try again.",
        )

    # ------------------------------------------------------------------
    # 6a. Enforce domain allowlist (GOOGLE_ALLOWED_LOGIN_DOMAINS)
    # ------------------------------------------------------------------
    if not is_login_domain_allowed(email):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Your email domain is not permitted to access this application. "
                "Please use your university account."
            ),
        )

    # ------------------------------------------------------------------
    # 6b. Upsert user in the database
    # ------------------------------------------------------------------
    user = _upsert_user(db, google_sub=google_sub, email=email, full_name=full_name)

    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been suspended. Please contact support.",
        )

    # ------------------------------------------------------------------
    # 7. Issue a JWT
    # ------------------------------------------------------------------
    jwt_token = create_access_token(
        user_id=str(user.id),
        role=user.role,
        email=user.email,
    )

    # ------------------------------------------------------------------
    # 8. Redirect to frontend (or return JSON for API/testing use)
    # ------------------------------------------------------------------
    if settings.frontend_url:
        # SPA flow: redirect to /auth/callback?token=…&role=…
        # The frontend reads these params, stores the token, and navigates
        # to the correct dashboard.
        redirect_url = (
            f"{settings.frontend_url.rstrip('/')}/auth/callback"
            f"?token={jwt_token}&role={user.role}"
        )
        response = RedirectResponse(url=redirect_url, status_code=302)
    else:
        # Headless/API-testing flow: just return JSON
        response = JSONResponse(
            content={
                "access_token": jwt_token,
                "token_type": "bearer",
                "role": user.role,
                "redirect_to": "/instructor" if user.role in ("instructor", "admin") else "/student",
                "user": {
                    "id": str(user.id),
                    "email": user.email,
                    "full_name": user.full_name,
                    "role": user.role,
                },
            }
        )

    return _clear_state_cookie(response)


# ---------------------------------------------------------------------------
# Route: current user profile
# ---------------------------------------------------------------------------

# @router.get(
#     "/me",
#     response_model=UserOut,
#     summary="Get current user profile",
#     description=(
#         "Returns the profile of the authenticated user. "
#         "Requires a valid Bearer JWT in the Authorization header."
#     ),
# )
# def get_current_user_profile(
#     current_user: User = Depends(get_current_user),
# ):
#     """Return the logged-in user's profile."""
#     return current_user


# ---------------------------------------------------------------------------
# Route: logout
# ---------------------------------------------------------------------------

# @router.post(
#     "/logout",
#     summary="Log out",
#     description=(
#         "For stateless JWTs the client simply discards its token. "
#         "This endpoint exists so the frontend has a clean call to make "
#         "and for future server-side token revocation."
#     ),
# )
# def logout():
#     """
#     Stateless logout — the client discards its JWT.
#     If a token blacklist / Redis revocation list is added later,
#     extract the token here via Depends(get_current_user) and insert it.
#     """
#     return {"detail": "Logged out successfully."}





# new endpoint

@router.get(
    "/google/login",
    summary="Integration",
)
def login_with_google(
    response: Response,
    Authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    if not Authorization or not Authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid Authorization header")

    token = Authorization[len("Bearer "):]

    userinfo = _fetch_google_userinfo(token)

    google_sub = userinfo.get("sub")
    email = userinfo.get("email")
    full_name = userinfo.get("name")
    image = userinfo.get("picture")

    if not google_sub or not email or not full_name:
        raise HTTPException(status_code=400, detail="Missing required Google user info")

    if not is_login_domain_allowed(email):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Your email domain is not permitted to access this application. "
                "Please use your university account."
            ),
        )

    user = _upsert_user(db, google_sub=google_sub, email=email, full_name=full_name, image=image)

    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been suspended. Please contact support.",
        )

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
        max_age=60 * 60 * 24,
    )


    return {
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "image": user.image,
        },
    }


@router.post("/google/logout",
             summary="Integration",
)
def logout(response: Response):
    response.delete_cookie(
        key="access_token",
        httponly=True,
        secure=False,
        samesite="lax",
    )
    return {"message": "Logged out"}



@router.get(
    "/google/me",
    response_model=UserOut,
    summary="Integration",
   
)
def get_user_info(
    current_user: User = Depends(get_current_user),
):

    return current_user




