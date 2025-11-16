from pydantic import BaseModel
from typing import Optional, Dict, Any


class ExtractProcessRequest(BaseModel):
    """Extract /process 요청 스키마"""
    fileNo: Optional[str] = None
    extractionStrategy: str
    extractionParameter: Dict[str, Any] = {}


class ExtractTestRequest(BaseModel):
    """Extract /test 요청 스키마 (Form 데이터용)"""
    extractionStrategy: str
    extractionParameter: Dict[Any, Any] = {}



