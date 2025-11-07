from __future__ import annotations

from typing import Generic, TypeVar
from pydantic import BaseModel


T = TypeVar("T")


class Result(BaseModel, Generic[T]):
    data: T
    pagination: "Pagination | None" = None


class BaseResponse(BaseModel, Generic[T]):
    status: int
    code: str
    message: str
    isSuccess: bool
    result: Result[T]


class Pagination(BaseModel):
    pageNum: int
    pageSize: int
    totalItems: int
    totalPages: int
    hasNext: bool

