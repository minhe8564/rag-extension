from pydantic import BaseModel
from typing import Dict, Any


class ErrorResponse(BaseModel):
    """에러 응답 스키마"""
    status: int
    code: str
    message: str
    isSuccess: bool
    result: Dict[str, Any]

