from pydantic import BaseModel
from typing import List, Dict, Any


class Page(BaseModel):
    """Page 스키마"""
    page: int
    content: str


class ExtractProcessResult(BaseModel):
    """Extract /process 결과 스키마"""
    fileName: str
    fileType: str
    pages: List[Page]
    total_pages: int
    strategy: str
    strategyParameter: Dict[str, Any]


class ExtractProcessResponse(BaseModel):
    """Extract /process 응답 스키마"""
    status: int
    code: str
    message: str
    isSuccess: bool
    result: ExtractProcessResult




