from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.enums import UserRole


# User

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    full_name: str
    upi: str
    role: UserRole
    image: str | None = None

class Userupi(BaseModel):
    # model_config = ConfigDict(from_attributes=True)

    upi: str

# Auth

class GoogleLoginResponse(BaseModel):
    user: UserResponse