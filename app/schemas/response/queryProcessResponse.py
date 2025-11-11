from pydantic import BaseModel
from typing import List, Dict, Any


class QueryProcessResult(BaseModel):
    """Query Process 결과 스키마 (final shape for client)"""
    messageNo: str
    role: str
    content: str
    createdAt: str


class QueryProcessResponse(BaseModel):
    """Query /process 응답 스키마"""
    status: int
    code: str
    message: str
    isSuccess: bool
    result: QueryProcessResult

