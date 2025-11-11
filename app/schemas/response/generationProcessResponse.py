from pydantic import BaseModel
from typing import List, Dict, Any


class Citation(BaseModel):
    """Citation 스키마"""
    text: str
    page: int
    chunk_id: int
    score: float


class GenerationProcessResult(BaseModel):
    """Generation Process 결과 스키마"""
    query: str
    answer: str
    citations: List[Citation]
    contexts_used: int
    strategy: str
    parameters: Dict[Any, Any]
    messageNo: str | None = None
    createdAt: str | None = None


class GenerationProcessResponse(BaseModel):
    """Generation /process 응답 스키마"""
    status: int
    code: str
    message: str
    isSuccess: bool
    result: GenerationProcessResult




