from uuid import UUID

from pydantic import BaseModel


class ReleaseResponse(BaseModel):
    sessions_created: int

