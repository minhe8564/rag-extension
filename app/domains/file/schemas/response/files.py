from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class FileListItem(BaseModel):
    fileNo: str
    name: str
    size: int
    type: str
    bucket: str
    path: str
    status: str
    categoryNo: str
    collectionNo: Optional[str] = None
    createdAt: datetime
