from __future__ import annotations

from pydantic import BaseModel


class FileCategoryListItem(BaseModel):
    categoryNo: str
    name: str

    class Config:
        from_attributes = True

