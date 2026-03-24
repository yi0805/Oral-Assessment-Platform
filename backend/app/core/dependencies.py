"""
Shared FastAPI dependencies (reusable across routes).

These are injected via FastAPI's Depends() mechanism.

TODO:
- get_current_user — extracts user from JWT token
- require_instructor — ensures user.role == 'instructor'
- require_student — ensures user.role == 'student'
- require_enrollment — ensures user is enrolled in the course
"""
# from fastapi import Depends, HTTPException, status
# from sqlalchemy.orm import Session
# from app.core.database import get_db
# from app.core.security import verify_token

# TODO: Implement auth dependencies here

pass
