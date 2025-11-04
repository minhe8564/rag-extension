from __future__ import annotations

from pydantic import BaseModel


class FileUploadResult(BaseModel):
    fileNo: str

