"""
표준 응답 스키마
"""
from typing import Generic, TypeVar, Optional
from pydantic import BaseModel

T = TypeVar('T')

class Result(BaseModel, Generic[T]):
    """결과 데이터 래퍼"""
    data: T

class BaseResponse(BaseModel, Generic[T]):
    """표준 API 응답 형식"""
    status: int
    code: str
    message: str
    isSuccess: bool
    result: Optional[Result[T]] = None