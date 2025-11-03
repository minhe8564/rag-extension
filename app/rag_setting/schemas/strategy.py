"""
RAG Strategy Schemas
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.rag_setting.models.strategy import binary_to_uuid


# ============================================
# StrategyType Schemas
# ============================================

class StrategyTypeBase(BaseModel):
    """StrategyType 기본 스키마"""
    name: str = Field(..., max_length=255, description="전략 유형 이름")


class StrategyTypeCreate(StrategyTypeBase):
    """StrategyType 생성 요청"""
    pass


class StrategyTypeResponse(StrategyTypeBase):
    """StrategyType 응답"""
    strategy_type_no: str = Field(..., description="전략 유형 ID (UUID)")
    created_at: datetime
    updated_at: datetime

    @validator("strategy_type_no", pre=True)
    def convert_binary_to_uuid(cls, v):
        """binary(16) → UUID 문자열 변환"""
        if isinstance(v, bytes):
            return binary_to_uuid(v)
        return v

    class Config:
        from_attributes = True


# ============================================
# Strategy Schemas
# ============================================

class StrategyBase(BaseModel):
    """Strategy 기본 스키마"""
    name: str = Field(..., max_length=50, description="전략명")
    description: str = Field(..., max_length=255, description="전략 설명")
    parameter: Optional[Dict[str, Any]] = Field(None, description="전략 파라미터 (JSON)")


class StrategyCreate(StrategyBase):
    """Strategy 생성 요청"""
    strategy_type_no: str = Field(..., description="전략 유형 ID (UUID)")


class StrategyUpdate(BaseModel):
    """Strategy 업데이트 요청"""
    name: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = Field(None, max_length=255)
    parameter: Optional[Dict[str, Any]] = None
    strategy_type_no: Optional[str] = None


class StrategyResponse(BaseModel):
    """Strategy 응답 (API 명세에 맞춤)"""
    strategyNo: str = Field(..., description="전략 ID (UUID)")
    name: str = Field(..., description="전략명")
    description: str = Field(..., description="전략 설명")
    type: str = Field(..., description="전략 유형 이름")
    parameter: Optional[Dict[str, Any]] = Field(None, description="전략 파라미터")

    class Config:
        from_attributes = True

    @classmethod
    def from_strategy(cls, strategy):
        """Strategy ORM 객체를 Pydantic 모델로 변환"""
        return cls(
            strategyNo=binary_to_uuid(strategy.strategy_no),
            name=strategy.name,
            description=strategy.description,
            type=strategy.strategy_type.name if strategy.strategy_type else "",
            parameter=strategy.parameter
        )


# ============================================
# Pagination & Response Schemas
# ============================================

class PaginationResponse(BaseModel):
    """페이지네이션 정보"""
    pageNum: int
    pageSize: int
    totalItems: int
    totalPages: int
    hasNext: bool


class StrategyListResult(BaseModel):
    """전략 목록 결과"""
    data: List[StrategyResponse]
    pagination: PaginationResponse


class StandardResponse(BaseModel):
    """표준 API 응답"""
    status: int
    code: str
    message: str
    isSuccess: bool
    result: StrategyListResult


class ErrorResponse(BaseModel):
    """에러 응답"""
    status: int
    code: str
    message: str
    isSuccess: bool
    result: dict = {}
