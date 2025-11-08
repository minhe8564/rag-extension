from __future__ import annotations

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
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


class StrategyWithParameter(BaseModel):
    """전략 + 파라미터 아이템"""
    no: str = Field(..., description="전략 ID (UUID)")
    parameters: Optional[Dict[str, Any]] = Field(
        None,
        description="전략별 파라미터",
        json_schema_extra={"example": {}}
    )


class StrategyDetail(BaseModel):
    """전략 상세 정보"""
    no: str = Field(..., description="전략 ID (UUID)")
    code: str = Field(..., description="전략 코드")
    name: str = Field(..., description="전략 이름")
    description: str = Field(..., description="전략 설명")
    parameters: Optional[Dict[str, Any]] = Field(
        None,
        description="전략별 파라미터",
    )


class IngestTemplateCreateRequest(BaseModel):
    """Ingest 템플릿 생성 요청"""
    name: str = Field(..., description="템플릿 이름", max_length=100)
    isDefault: bool = Field(False, description="기본 템플릿 여부")
    extractions: List[StrategyWithParameter] = Field(..., description="추출 전략 목록")
    chunking: StrategyWithParameter = Field(..., description="청킹 전략")
    denseEmbeddings: List[StrategyWithParameter] = Field(..., description="밀집 임베딩 전략 목록")
    sparseEmbedding: StrategyWithParameter = Field(..., description="희소 임베딩 전략")

    class Config:
        json_schema_extra = {
            "example": {
                "isDefault": False,
                "name": "기본 RAG 템플릿",
                "extractions": [
                    {
                        "no": "0dd1cd24-3459-4080-9c0a-6a7bba85a3e4",
                        "parameters": {}
                    }
                ],
                "chunking": {
                    "no": "2014c312-1284-4e06-bec5-327c42f6bc3b",
                    "parameters": {
                        "overlap": 40,
                        "token": 512
                    }
                },
                "denseEmbeddings": [
                    {
                        "no": "adb8865e-fc06-4256-8a56-7cdcfea32651",
                        "parameters": {}
                    }
                ],
                "sparseEmbedding": {
                    "no": "b278151f-3439-45fa-abc9-d6173cb659c8",
                    "parameters": {}
                }
            }
        }


class IngestTemplatePartialUpdateRequest(BaseModel):
    """Ingest 템플릿 부분 수정 요청"""
    name: Optional[str] = Field(None, description="템플릿 이름", max_length=100)
    isDefault: Optional[bool] = Field(None, description="기본 템플릿 여부")
    extractions: Optional[List[StrategyWithParameter]] = Field(None, description="추출 전략 목록")
    chunking: Optional[StrategyWithParameter] = Field(None, description="청킹 전략")
    denseEmbeddings: Optional[List[StrategyWithParameter]] = Field(None, description="밀집 임베딩 전략 목록")
    sparseEmbedding: Optional[StrategyWithParameter] = Field(None, description="희소 임베딩 전략")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "듀얼 임베딩 템플릿",
                "isDefault": True,
                "chunking": {
                    "no": "2014c312-1284-4e06-bec5-327c42f6bc3b",
                    "parameters": {
                        "token": 1024,
                        "overlap": 80
                    }
                },
                "sparseEmbedding": {
                    "no": "adb8865e-fc06-4256-8a56-7cdcfea32651"
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
    extractions: List[StrategyDetail] = Field(..., description="추출 전략 목록")
    chunking: StrategyDetail = Field(..., description="청킹 전략")
    denseEmbeddings: List[StrategyDetail] = Field(..., description="밀집 임베딩 전략 목록")
    sparseEmbedding: StrategyDetail = Field(..., description="희소 임베딩 전략")


class IngestTemplateUpdateRequest(BaseModel):
    """Ingest 템플릿 수정 요청"""
    name: str = Field(..., description="템플릿 이름", max_length=100)
    isDefault: bool = Field(False, description="기본 템플릿 여부")
    extractions: List[StrategyWithParameter] = Field(..., description="추출 전략 목록")
    chunking: StrategyWithParameter = Field(..., description="청킹 전략")
    denseEmbeddings: List[StrategyWithParameter] = Field(..., description="밀집 임베딩 전략 목록")
    sparseEmbedding: StrategyWithParameter = Field(..., description="희소 임베딩 전략")

    class Config:
        json_schema_extra = {
            "example": {
                "isDefault": True,
                "name": "기본 RAG 템플릿",
                "extractions": [
                    {
                    "no": "0dd1cd24-3459-4080-9c0a-6a7bba85a3e4",
                    "parameters": {}
                    }
                ],
                "chunking": {
                    "no": "2014c312-1284-4e06-bec5-327c42f6bc3b",
                    "parameters": {
                    "overlap": 40,
                    "token": 512
                    }
                },
                "denseEmbeddings": [
                    {
                    "no": "adb8865e-fc06-4256-8a56-7cdcfea32651",
                    "parameters": {}
                    }
                ],
                "sparseEmbedding": {
                    "no": "b278151f-3439-45fa-abc9-d6173cb659c8",
                    "parameters": {}
                }
            }
        }
