from typing import List, Optional
from pydantic import BaseModel


class FileInfo(BaseModel):
    """파일 정보"""
    fileNo: str
    fileType: str
    fileName: str
    path: str


class IngestProcessRequest(BaseModel):
    """Ingest /process 요청 스키마 (userRole은 헤더로 수신)"""
    bucket: str
    offerNo: str
    files: List[FileInfo]