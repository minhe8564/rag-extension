from __future__ import annotations

from pydantic import BaseModel
from datetime import datetime


class TestCollectionListItem(BaseModel):
    testCollectionNo: str
    name: str
    ingestNo: str
    createdAt: datetime

    class Config:
        from_attributes = True
