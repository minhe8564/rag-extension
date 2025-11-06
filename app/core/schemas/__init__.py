from __future__ import annotations

from typing import Generic, TypeVar
from pydantic import BaseModel


T = TypeVar("T")


class Result(BaseModel, Generic[T]):
    data: T


class BaseResponse(BaseModel, Generic[T]):
    status: int
    code: str
    message: str
    isSuccess: bool
    result: Result[T]