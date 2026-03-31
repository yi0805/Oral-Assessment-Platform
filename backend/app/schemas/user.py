"""Pydantic schemas for user-related API requests and responses."""
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict
from app.schemas.enums import UserRole


class UserBase(BaseModel):
    """Shared fields for user schemas."""
    email: str
    full_name: str
    role: UserRole


class UserCreate(BaseModel):
    """
    Created internally when Google OAuth callback fires.
    The frontend never sends this directly — it comes from the OAuth provider.
    """
    google_sub: str
    email: str
    full_name: str
    role: UserRole = UserRole.student


class UserUpdate(BaseModel):
    """Fields an admin can update on an existing user."""
    full_name: str | None = None
    role: UserRole | None = None
    status: str | None = None


class UserOut(BaseModel):
    """Returned by GET /auth/me and embedded in other responses."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    full_name: str
    role: UserRole
    status: str
    created_at: datetime


class UserBrief(BaseModel):
    """Minimal user info embedded in lists (e.g. student list, enrollment list)."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    full_name: str
    role: UserRole
