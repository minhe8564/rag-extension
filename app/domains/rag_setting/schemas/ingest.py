from __future__ import annotations

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, ConfigDict
from .strategy import PaginationInfo


class IngestGroupListItem(BaseModel):
    """Ingest 그룹 목록 아이템"""
    ingestNo: str = Field(..., description="Ingest 그룹 ID (UUID)")
    name: str = Field(..., description="템플릿 이름")
    isDefault: bool = Field(..., description="기본 템플릿 여부")

    class Config:
        from_attributes = True


class IngestGroupListResponse(BaseModel):
    """Ingest 그룹 목록 응답"""
    data: List[IngestGroupListItem] = Field(..., description="Ingest 템플릿 목록")
    pagination: PaginationInfo = Field(..., description="페이지네이션 정보")


class StrategyItem(BaseModel):
    """전략 아이템"""
    no: str = Field(..., description="전략 ID (UUID)")
    code: str = Field(..., description="전략 코드")
    name: str = Field(..., description="전략 이름")
    description: str = Field(..., description="전략 설명")
    parameters: Optional[Dict[str, Any]] = Field(
        None,
        description="전략별 파라미터",
        json_schema_extra={"example": {}}
    )


class IngestTemplateCreateRequest(BaseModel):
    """Ingest 템플릿 생성 요청"""
    name: str = Field(..., description="템플릿 이름", max_length=100)
    isDefault: bool = Field(False, description="기본 템플릿 여부")
    extractions: List[StrategyItem] = Field(..., description="추출 전략 목록")
    chunking: StrategyItem = Field(..., description="청킹 전략")
    denseEmbeddings: List[StrategyItem] = Field(..., description="밀집 임베딩 전략 목록")
    spareEmbedding: StrategyItem = Field(..., description="희소 임베딩 전략")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "기본 RAG 템플릿",
                "isDefault": False,
                "extractions": [
                    {
                        "no": "string",
                        "code": "strategy-code",
                        "name": "string",
                        "description": "string",
                        "parameters": {}
                    }
                ],
                "chunking": {
                    "no": "string",
                    "code": "chunking-code",
                    "name": "string",
                    "description": "string",
                    "parameters": {}
                },
                "denseEmbeddings": [
                    {
                        "no": "string",
                        "code": "strategy-code",
                        "name": "string",
                        "description": "string",
                        "parameters": {}
                    }
                ],
                "spareEmbedding": {
                    "no": "string",
                    "code": "embedding-code",
                    "name": "string",
                    "description": "string",
                    "parameters": {}
                }
            }
        }


class IngestTemplateCreateResponse(BaseModel):
    """Ingest 템플릿 생성 응답"""
    ingestNo: str = Field(..., description="생성된 Ingest 템플릿 ID (UUID)")


class InvalidInputError(BaseModel):
    """잘못된 입력 에러 응답"""
    missing: List[str] = Field(..., description="누락된 필드 목록")


class IngestTemplateDetailResponse(BaseModel):
    """Ingest 템플릿 상세 조회 응답"""
    ingestNo: str = Field(..., description="Ingest 템플릿 ID (UUID)")
    name: str = Field(..., description="템플릿 이름")
    isDefault: bool = Field(..., description="기본 템플릿 여부")
    extractions: List[StrategyItem] = Field(..., description="추출 전략 목록")
    chunking: StrategyItem = Field(..., description="청킹 전략")
    denseEmbeddings: List[StrategyItem] = Field(..., description="밀집 임베딩 전략 목록")
    spareEmbedding: StrategyItem = Field(..., description="희소 임베딩 전략")


class StrategyUpdateItem(BaseModel):
    """전략 수정 아이템 (간소화 버전)"""
    no: str = Field(..., description="전략 ID (UUID)")
    parameters: Optional[Dict[str, Any]] = Field(
        None,
        description="전략별 파라미터",
        json_schema_extra={"example": {}}
    )


class IngestTemplateUpdateRequest(BaseModel):
    """Ingest 템플릿 수정 요청"""
    name: str = Field(..., description="템플릿 이름", max_length=100)
    isDefault: bool = Field(False, description="기본 템플릿 여부")
    extractions: List[StrategyUpdateItem] = Field(..., description="추출 전략 목록")
    chunking: StrategyUpdateItem = Field(..., description="청킹 전략")
    denseEmbeddings: List[StrategyUpdateItem] = Field(..., description="밀집 임베딩 전략 목록")
    spareEmbedding: StrategyUpdateItem = Field(..., description="희소 임베딩 전략")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "기본 Ingest 템플릿",
                "extractions": [
                    {"no": "string", "parameters": {}}
                ],
                "chunking": {
                    "no": "string",
                    "parameters": {}
                },
                "denseEmbeddings": [
                    {"no": "string", "parameters": {}}
                ],
                "spareEmbedding": {
                    "no": "string",
                    "parameters": {}
                }
            }
        }
