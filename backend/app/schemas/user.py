from uuid import UUID
from pydantic import BaseModel,ConfigDict
from app.schemas.enums import UserRole


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    email: str
    full_name: str
    role: UserRole
    image: str | None = None


class GoogleLoginResponse(BaseModel):
    user: UserResponse