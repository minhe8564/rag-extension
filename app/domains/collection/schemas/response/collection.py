from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel


class CollectionListItem(BaseModel):
    collectionNo: str
    createdAt: datetime

    class Config:
        from_attributes = True
