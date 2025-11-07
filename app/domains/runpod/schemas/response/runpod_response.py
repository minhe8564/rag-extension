from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel


class RunpodListItem(BaseModel):
    """Runpod 목록 항목"""
    runpodNo: str
    name: str
    address: str
    createdAt: datetime
    updatedAt: datetime


class RunpodResponse(BaseModel):
    """Runpod 상세 응답"""
    runpodNo: str
    name: str
    address: str
    createdAt: datetime
    updatedAt: datetime

