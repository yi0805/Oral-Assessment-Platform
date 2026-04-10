from uuid import UUID
from pydantic import BaseModel, EmailStr,ConfigDict
from app.schemas.enums import UserRole


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    email: EmailStr
    full_name: str
    role: UserRole
    image: str | None = None


class GoogleLoginResponse(BaseModel):
    user: UserResponse