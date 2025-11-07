from __future__ import annotations

from typing import Optional, Dict, Any, List
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


class StrategyCreateRequest(BaseModel):
    """전략 생성 요청 본문"""
    name: str = Field(..., min_length=1, max_length=50, description="전략명")
    description: str = Field(..., min_length=1, max_length=255, description="전략 설명")
    parameter: Optional[Dict[str, Any]] = Field(None, description="전략 파라미터")
    strategyType: str = Field(..., min_length=1, max_length=255, description="전략 유형 이름")


class StrategyCreateResponse(BaseModel):
    """전략 생성 응답"""
    strategyNo: str = Field(..., description="생성된 전략 ID (UUID)")


class StrategyUpdateRequest(BaseModel):
    """전략 수정 요청"""
    name: str = Field(..., min_length=1, max_length=50, description="전략명")
    description: str = Field(..., min_length=1, max_length=255, description="전략 설명")
    parameter: Optional[Dict[str, Any]] = Field(None, description="전략 파라미터")
    strategyType: Optional[str] = Field(None, min_length=1, max_length=255, description="전략 유형 이름")


class StrategyUpdateResponse(BaseModel):
    """전략 수정 응답"""
    strategyNo: str = Field(..., description="전략 ID (UUID)")
    name: str = Field(..., description="전략명")
    description: str = Field(..., description="전략 설명")
    type: str = Field(..., description="전략 유형 이름")
    parameter: Optional[Dict[str, Any]] = Field(None, description="전략 파라미터")


class StrategyTypeListItem(BaseModel):
    """전략 유형 목록 아이템"""
    strategyTypeNo: str = Field(..., description="전략 유형 ID (UUID)")
    name: str = Field(..., description="전략 유형 이름")


class StrategyTypeListResponse(BaseModel):
    """전략 유형 목록 응답 데이터"""
    data: List[StrategyTypeListItem]


class StrategyTypeCreateRequest(BaseModel):
    """전략 유형 생성 요청"""
    name: str = Field(..., min_length=1, max_length=255, description="전략 유형 이름")


class StrategyTypeCreateResponse(BaseModel):
    """전략 유형 생성 응답"""
    strategyTypeNo: str = Field(..., description="생성된 전략 유형 ID (UUID)")


class StrategyTypeUpdateRequest(BaseModel):
    """전략 유형 수정 요청"""
    name: str = Field(..., min_length=1, max_length=255, description="수정할 전략 유형 이름")


class StrategyTypeUpdateResponse(BaseModel):
    """전략 유형 수정 응답"""
    strategyTypeNo: str = Field(..., description="전략 유형 ID (UUID)")
    name: str = Field(..., description="수정된 전략 유형 이름")