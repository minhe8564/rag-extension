from pydantic import BaseModel
from typing import List, Dict, Any


class Citation(BaseModel):
    """Citation 스키마"""
    text: str
    page: int
    chunk_id: int
    score: float


class QueryProcessResult(BaseModel):
    """Query Process 결과 스키마"""
    query: str
    answer: str
    citations: List[Citation]


class QueryProcessResponse(BaseModel):
    """Query /process 응답 스키마"""
    status: int
    code: str
    message: str
    isSuccess: bool
    result: QueryProcessResult

