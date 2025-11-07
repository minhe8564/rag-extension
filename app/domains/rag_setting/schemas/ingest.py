from __future__ import annotations

from typing import Dict, Any, List, Optional
import uuid
from pydantic import BaseModel, Field, ConfigDict, field_validator
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
    name: str = Field(..., description="전략 이름")
    description: str = Field(..., description="전략 설명")
    parameters: Optional[Dict[str, Any]] = Field(
        None,
        description="전략별 파라미터",
        json_schema_extra={"example": {}}
    )

    @field_validator('no')
    @classmethod
    def validate_uuid(cls, v: str) -> str:
        """UUID 형식 검증"""
        try:
            uuid.UUID(v)
            return v
        except (ValueError, AttributeError):
            raise ValueError(f"올바르지 않은 UUID 형식입니다: {v}")

    @classmethod
    def from_strategy(cls, strategy) -> "StrategyItem":
        """
        Strategy 모델 객체로부터 StrategyItem 생성

        Args:
            strategy: Strategy 모델 객체

        Returns:
            StrategyItem 인스턴스
        """
        # UUID를 문자열로 변환 (bytes → str)
        uuid_str = str(uuid.UUID(bytes=strategy.strategy_no))

        return cls(
            no=uuid_str,
            name=strategy.name,
            description=strategy.description or "",
            parameters=strategy.parameter or {}
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
                        "name": "string",
                        "description": "string",
                        "parameters": {}
                    }
                ],
                "chunking": {
                    "no": "string",
                    "name": "string",
                    "description": "string",
                    "parameters": {}
                },
                "denseEmbeddings": [
                    {
                        "no": "string",
                        "name": "string",
                        "description": "string",
                        "parameters": {}
                    }
                ],
                "spareEmbedding": {
                    "no": "string",
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

    @classmethod
    def from_ingest_group(cls, ingest_group) -> "IngestTemplateDetailResponse":
        """
        IngestGroup 모델 객체로부터 IngestTemplateDetailResponse 생성

        Args:
            ingest_group: IngestGroup 모델 객체 (extraction_groups, embedding_groups 관계 포함)

        Returns:
            IngestTemplateDetailResponse 인스턴스
        """
        # UUID를 문자열로 변환 (bytes → str)
        uuid_str = str(uuid.UUID(bytes=ingest_group.ingest_group_no))

        # extraction_groups에서 추출 전략 리스트 생성
        extractions = [
            StrategyItem.from_strategy(ext_group.extraction_strategy)
            for ext_group in ingest_group.extraction_groups
        ]

        # embedding_groups에서 임베딩 전략 리스트 생성
        embeddings = [
            StrategyItem.from_strategy(emb_group.embedding_strategy)
            for emb_group in ingest_group.embedding_groups
        ]

        # denseEmbeddings와 spareEmbedding은 동일한 리스트 사용
        # (기존 스키마 구조를 유지하기 위해 embeddings를 두 필드 모두에 사용)
        return cls(
            ingestNo=uuid_str,
            name=ingest_group.name,
            isDefault=ingest_group.is_default,
            extractions=extractions,
            chunking=StrategyItem.from_strategy(ingest_group.chunking_strategy),
            denseEmbeddings=embeddings,
            spareEmbedding=embeddings[0] if embeddings else StrategyItem.from_strategy(ingest_group.chunking_strategy),
        )


class StrategyUpdateItem(BaseModel):
    """전략 수정 아이템 (간소화 버전)"""
    no: str = Field(..., description="전략 ID (UUID)")
    parameters: Optional[Dict[str, Any]] = Field(
        None,
        description="전략별 파라미터",
        json_schema_extra={"example": {}}
    )

    @field_validator('no')
    @classmethod
    def validate_uuid(cls, v: str) -> str:
        """UUID 형식 검증"""
        try:
            uuid.UUID(v)
            return v
        except (ValueError, AttributeError):
            raise ValueError(f"올바르지 않은 UUID 형식입니다: {v}")


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
