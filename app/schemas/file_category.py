from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field


class FileCategoryOut(BaseModel):
    file_category_no: str = Field(description="Primary key in hex string (16-byte BINARY)")
    name: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

