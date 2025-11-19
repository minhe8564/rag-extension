from pydantic import BaseModel
from typing import Dict, Any, List


class IngestProcessResult(BaseModel):
    """Ingest /process 결과 스키마"""
    completed: List[str]
    failed: List[str]
    collectionName: str


class IngestProcessResponse(BaseModel):
    """Ingest /process 응답 스키마"""
    status: int
    code: str
    message: str
    isSuccess: bool
    result: IngestProcessResult
