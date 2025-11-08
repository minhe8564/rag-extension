from __future__ import annotations

from typing import Generic, TypeVar, Dict, Any, Optional
from pydantic import BaseModel, ConfigDict
from app.core.cursor import CursorParams

T = TypeVar("T")


class Result(BaseModel, Generic[T]):
    data: T
    pagination: "Pagination | None" = None
    hasNext: Optional[bool] = None
    nextCursor: Optional[CursorParams] = None
    
    # Null 값 제외 설정
    model_config = ConfigDict(exclude_none=True)


class BaseResponse(BaseModel, Generic[T]):
    status: int
    code: str
    message: str
    isSuccess: bool
    result: Result[T] | Dict[str, Any] | T


class Pagination(BaseModel):
    pageNum: int
    pageSize: int
    totalItems: int
    totalPages: int
    hasNext: bool

