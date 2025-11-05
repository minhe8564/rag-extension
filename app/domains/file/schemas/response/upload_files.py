from __future__ import annotations

from pydantic import BaseModel
from typing import List


class FileUploadBatchResult(BaseModel):
    fileNos: List[str]


class IngestFileMeta(BaseModel):
    fileNo: str
    fileType: str
    fileName: str
    path: str


class UploadBatchMeta(BaseModel):
    bucket: str
    offerNo: str
    files: List[IngestFileMeta]

