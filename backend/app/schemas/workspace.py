from datetime import datetime

from pydantic import BaseModel


class WorkspaceCreate(BaseModel):
    name: str
    description: str = ""


class WorkspaceRead(BaseModel):
    id: int
    name: str
    description: str
    created_at: datetime | None = None
    updated_at: datetime | None = None
