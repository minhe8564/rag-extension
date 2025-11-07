from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel


class TestFileListItem(BaseModel):
    testFileNo: str
    name: str
    size: int
    type: str
    hash: str
    description: str
    bucket: str
    path: str
    createdAt: datetime

    class Config:
        from_attributes = True

