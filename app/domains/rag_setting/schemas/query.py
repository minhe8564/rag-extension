from __future__ import annotations

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field, ConfigDict
from .strategy import PaginationInfo


class StrategyWithParameter(BaseModel):
    """전략 + 파라미터 아이템"""
    no: str = Field(..., description="전략 ID (UUID)")
    parameters: Optional[Dict[str, Any]] = Field(
        None,
        description="전략별 파라미터",
        json_schema_extra={"example": {}}
    )


class QueryTemplateCreateRequest(BaseModel):
    """Query 템플릿 생성 요청"""
    name: str = Field(..., description="템플릿 이름", max_length=100)
    transformation: StrategyWithParameter = Field(..., description="변환 전략")
    retrieval: StrategyWithParameter = Field(..., description="검색 전략")
    reranking: StrategyWithParameter = Field(..., description="재순위화 전략")
    systemPrompt: StrategyWithParameter = Field(..., description="시스템 프롬프트 전략")
    userPrompt: StrategyWithParameter = Field(..., description="사용자 프롬프트 전략")
    generation: StrategyWithParameter = Field(..., description="생성 전략")
    isDefault: bool = Field(False, description="기본 템플릿 여부", json_schema_extra={"example": False})

    class Config:
        json_schema_extra = {
            "example": {
                "name": "기본 Query 템플릿",
                "transformation": {
                    "no": "16a2ca46-4701-4fa7-98a4-17397c20a0ae"
                },
                "retrieval": {
                    "no": "f315a3d9-70ba-466a-b0a5-bf695a952f5b",
                    "parameters": {
                        "semantic": {
                            "topK": 20,
                            "threshold": 0.6
                        },
                        "keyword": {
                            "topK": 20
                        },
                        "reranker": {
                            "type": "weighted",
                            "weight": 0.4,
                            "topK": 10
                        }
                    }
                },
                "reranking": {
                    "no": "65d58009-d777-4bb9-b2e2-73a548cfdde1",
                    "parameters": {
                        "topK": 5
                    }
                },
                "systemPrompt": {
                    "no": "4e777331-ae8d-4f27-85ae-e905eeb2b6a8"
                },
                "userPrompt": {
                    "no": "e1f2a9fe-0ecc-4098-8c90-bfd3f8accecc"
                },
                "generation": {
                    "no": "6cd296cf-efb5-4037-a932-fd2b78820ea8",
                    "parameters": {
                        "temperature": 0.3,
                        "timeout": 100,
                        "maxRetries": 5,
                        "stop": ["그만"],
                        "maxTokens": 768,
                        "topP": 0.95
                    }
                },
                "isDefault": False
            }
        }


class QueryTemplateCreateResponse(BaseModel):
    """Query 템플릿 생성 응답"""
    queryNo: str = Field(..., description="생성된 Query 템플릿 ID (UUID)")


class QueryTemplateListItem(BaseModel):
    """Query 템플릿 목록 아이템"""
    queryNo: str = Field(..., description="Query 템플릿 ID (UUID)")
    name: str = Field(..., description="템플릿 이름")
    isDefault: bool = Field(..., description="기본 템플릿 여부")

    class Config:
        from_attributes = True


class QueryTemplateListResponse(BaseModel):
    """Query 템플릿 목록 응답"""
    data: List[QueryTemplateListItem] = Field(..., description="Query 템플릿 목록")
    pagination: PaginationInfo = Field(..., description="페이지네이션 정보")


class StrategyDetail(BaseModel):
    """전략 상세 정보"""
    no: str = Field(..., description="전략 ID (UUID)")
    code: str = Field(..., description="전략 코드")
    name: str = Field(..., description="전략명")
    description: str = Field(..., description="전략 설명")
    parameters: Optional[Dict[str, Any]] = Field(None, description="전략 파라미터")


class QueryTemplateDetailResponse(BaseModel):
    """Query 템플릿 상세 응답"""
    queryNo: str = Field(..., description="Query 템플릿 ID (UUID)")
    name: str = Field(..., description="템플릿 이름")
    isDefault: bool = Field(..., description="기본 템플릿 여부")
    transformation: StrategyDetail = Field(..., description="변환 전략")
    retrieval: StrategyDetail = Field(..., description="검색 전략")
    reranking: StrategyDetail = Field(..., description="재순위화 전략")
    systemPrompt: StrategyDetail = Field(..., description="시스템 프롬프트 전략")
    userPrompt: StrategyDetail = Field(..., description="사용자 프롬프트 전략")
    generation: StrategyDetail = Field(..., description="생성 전략")


class QueryTemplateUpdateRequest(BaseModel):
    """Query 템플릿 수정 요청"""
    name: str = Field(..., description="템플릿 이름", min_length=1, max_length=50)
    transformation: StrategyWithParameter = Field(..., description="변환 전략")
    retrieval: StrategyWithParameter = Field(..., description="검색 전략")
    reranking: StrategyWithParameter = Field(..., description="재순위화 전략")
    systemPrompt: StrategyWithParameter = Field(..., description="시스템 프롬프트 전략")
    userPrompt: StrategyWithParameter = Field(..., description="사용자 프롬프트 전략")
    generation: StrategyWithParameter = Field(..., description="생성 전략")
    isDefault: Optional[bool] = Field(None, description="기본 템플릿 여부")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "수정된 Query 템플릿",
                "transformation": {
                    "no": "21d396bd-8f78-4f86-8211-c0c030f9ed60"
                },
                "retrieval": {
                    "no": "d8139f0e-8ca2-4746-af19-7f5bab30ec2f",
                    "parameters": {
                        "semantic": {"topK": 20, "threshold": 0.6},
                        "keyword": {"topK": 20},
                        "reranker": {"type": "weighted", "weight": 0.4, "top_k": 10}
                    }
                },
                "reranking": {
                    "no": "e9f83976-e8ad-4aa6-b6cc-2fd530f4478c",
                    "parameters": {"topK": 5}
                },
                "systemPrompt": {
                    "no": "9b9f5730-f70f-41b2-b6d5-f8c71a1fb4a6"
                },
                "userPrompt": {
                    "no": "d8139f0e-8ca2-4746-af19-7f5bab30ec2f"
                },
                "generation": {
                    "no": "5ead8b24-c974-466c-ac42-42325ff26f2d",
                    "parameters": {
                        "temperature": 0.3,
                        "timeout": 100,
                        "maxRetries": 5,
                        "stop": ["그만"],
                        "max_tokens": 768,
                        "topP": 0.95
                    }
                },
                "isDefault": True
            }
        }
