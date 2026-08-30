from uuid import UUID

from pydantic import BaseModel


class GithubImportBody(BaseModel):
    url: str
    ref: str | None = None


class MaterialUploadOut(BaseModel):
    id: UUID
    processing_status: str


class MaterialStatusOut(MaterialUploadOut):
    filename: str
    is_processing_stale: bool = False
