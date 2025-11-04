from __future__ import annotations

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class StrategyListItem(BaseModel):
    """전략 목록 아이템"""
    strategyNo: str = Field(..., description="전략 ID (UUID)")
    name: str = Field(..., description="전략명")
    description: str = Field(..., description="전략 설명")
    type: str = Field(..., description="전략 유형 이름")
    parameter: Optional[Dict[str, Any]] = Field(None, description="전략 파라미터")

    class Config:
        from_attributes = True


class StrategyDetailResponse(BaseModel):
    """전략 상세 정보"""
    strategyNo: str = Field(..., description="전략 ID (UUID)")
    name: str = Field(..., description="전략명")
    description: str = Field(..., description="전략 설명")
    type: str = Field(..., description="전략 유형 이름")
    parameters: Optional[Dict[str, Any]] = Field(None, description="전략 파라미터")

    class Config:
        from_attributes = True


class PaginationInfo(BaseModel):
    """페이지네이션 정보"""
    pageNum: int
    pageSize: int
    totalItems: int
    totalPages: int
    hasNext: bool
