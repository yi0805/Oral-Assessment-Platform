"""
Auth routes: Google OAuth login/callback, JWT, user profile.

Endpoints:
  GET /auth/google/login → redirect to Google consent screen
  GET /auth/google/callback → handle callback, create/update user, return JWT
  GET /auth/me → return current user profile from JWT
  POST /auth/logout → invalidate session

TODO:
- [ ] Implement Google OAuth redirect
- [ ] Implement callback handler (create user in DB if new)
- [ ] Implement JWT issuance
- [ ] Implement /auth/me with get_current_user dependency
"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.schemas.user import UserOut, UserCreate

router = APIRouter()


@router.get("/google/login")
def google_login():
    """Redirect the user to Google's OAuth 2.0 consent screen."""
    # TODO: Build the Google OAuth authorization URL using settings.google_client_id
    # and redirect the user there. The redirect_uri should point to /auth/google/callback.
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Google OAuth login not yet implemented",
    )


@router.get("/google/callback")
def google_callback(code: str, db: Session = Depends(get_db)):
    """
    Handle the OAuth callback from Google.
    1. Exchange the authorization code for tokens
    2. Extract user info (email, name, google_sub) from the ID token
    3. Create or update the user in the database
    4. Issue a JWT access token and return it
    """
    # TODO: Exchange code for tokens via Google's token endpoint
    # TODO: Decode ID token to get user info
    # TODO: Upsert user in DB (create if new, update if existing)
    # TODO: Generate JWT with user_id and role as claims
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Google OAuth callback not yet implemented",
    )


@router.get("/me", response_model=UserOut)
def get_current_user_profile(db: Session = Depends(get_db)):
    """
    Return the current user's profile based on their JWT token.
    This is the first endpoint the frontend calls after login to get user info.
    """
    # TODO: Extract user_id from JWT via get_current_user dependency
    # TODO: Query DB for user and return UserOut
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Auth /me not yet implemented",
    )


@router.post("/logout")
def logout():
    """Invalidate the current session/token."""
    # TODO: If using server-side token blacklist, add token to blacklist
    # For stateless JWT, the frontend simply discards the token
    return {"detail": "Logged out successfully"}

