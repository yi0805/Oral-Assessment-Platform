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
from fastapi import APIRouter

router = APIRouter()

# TODO: Implement auth endpoints
