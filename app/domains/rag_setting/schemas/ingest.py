from __future__ import annotations

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class IngestGroupListItem(BaseModel):
    """Ingest 그룹 목록 아이템"""
    ingestNo: str = Field(..., description="Ingest 그룹 ID (UUID)")
    isDefault: bool = Field(..., description="기본 템플릿 여부")
    extractionStrategy: Dict[str, Any] = Field(..., description="추출 전략 정보")
    chunkingStrategy: Dict[str, Any] = Field(..., description="청킹 전략 정보")
    embeddingStrategy: Dict[str, Any] = Field(..., description="임베딩 전략 정보")

    class Config:
        from_attributes = True


class StrategyItem(BaseModel):
    """전략 아이템"""
    no: str = Field(..., description="전략 ID (UUID)")
    name: str = Field(..., description="전략 이름")
    description: str = Field(..., description="전략 설명")
    parameters: Optional[Dict[str, Any]] = Field(None, description="추가 파라미터")


class IngestTemplateCreateRequest(BaseModel):
    """Ingest 템플릿 생성 요청"""
    name: str = Field(..., description="템플릿 이름")
    isDefault: bool = Field(False, description="기본 템플릿 여부")
    extractions: List[StrategyItem] = Field(..., description="추출 전략 목록")
    chunking: StrategyItem = Field(..., description="청킹 전략")
    denseEmbeddings: List[StrategyItem] = Field(..., description="밀집 임베딩 전략 목록")
    spareEmbedding: StrategyItem = Field(..., description="희소 임베딩 전략")


class IngestTemplateCreateResponse(BaseModel):
    """Ingest 템플릿 생성 응답"""
    ingestNo: str = Field(..., description="생성된 Ingest 템플릿 ID (UUID)")


class InvalidInputError(BaseModel):
    """잘못된 입력 에러 응답"""
    missing: List[str] = Field(..., description="누락된 필드 목록")
