from pydantic import BaseModel
from typing import Dict, Any


class IngestTestResult(BaseModel):
    """Ingest /test 결과 스키마"""
    fileName: str
    collectionName: str


class IngestTestResponse(BaseModel):
    """Ingest /test 응답 스키마"""
    status: int
    code: str
    message: str
    isSuccess: bool
    result: IngestTestResult






