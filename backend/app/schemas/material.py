from pydantic import BaseModel


class GithubImportBody(BaseModel):
    url: str
    ref: str | None = None