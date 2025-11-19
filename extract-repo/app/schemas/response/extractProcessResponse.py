from pydantic import BaseModel
from typing import Dict, Any


class ExtractProcessResult(BaseModel):
    """Extract /process 결과 스키마"""
    fileName: str
    fileType: str
    strategy: str
    strategyParameter: Dict[str, Any]
    bucket: str | None = None
    path: str | None = None


class ExtractProcessResponse(BaseModel):
    """Extract /process 응답 스키마"""
    status: int
    code: str
    message: str
    isSuccess: bool
    result: ExtractProcessResult




