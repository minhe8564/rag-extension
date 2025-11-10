from __future__ import annotations

from typing import Dict, Any, Optional, List
import uuid
from pydantic import BaseModel, Field, ConfigDict, field_validator
from .strategy import PaginationInfo


class StrategyWithParameter(BaseModel):
    """전략 + 파라미터 아이템"""
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
                "isDefault": False,
                "name": "기본 Query 템플릿",
                "transformation": {
                    "no": "4b7c93a9-ca03-4caf-94e1-2ad5a4a64be1"
                },
                "reranking": {
                    "no": "ab4754a9-36b7-42b5-a0fe-64bc3de94596",
                    "parameters": {
                        "topK": 5, 
                    }
                },
                "retrieval": {
                    "no": "e9d321a3-98f2-4917-879b-d5407f14c44d",
                    "parameters": {
                        "type": "semantic", 
                        "sematic": {
                            "topK": 30, 
                            "threshold": 0.4
                        }
                    }
                },
                "systemPrompt": {
                    "no": "6bff6262-90a6-4eb1-bfc1-78bdd342c317"
                },
                "userPrompt": {
                    "no": "9c6a37bc-ef9b-4776-928c-f45c9eb65934"
                },
                "generation": {
                    "no": "bd3b754c-fd66-4a79-9cd9-3a13cebb17a1",
                    "parameters": {
                        "timeout": 30, 
                        "max_tokens": 512, 
                        "max_retries": 2, 
                        "temperature": 0.2
                    }
                }
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

    @classmethod
    def from_strategy(cls, strategy, parameters: Optional[Dict[str, Any]] = None) -> "StrategyDetail":
        """
        Strategy 모델 객체로부터 StrategyDetail 생성

        Args:
            strategy: Strategy 모델 객체
            parameters: 전략 파라미터 (없으면 빈 딕셔너리)

        Returns:
            StrategyDetail 인스턴스
        """
        from ..models.query_template import binary_to_uuid

        return cls(
            no=binary_to_uuid(strategy.strategy_no),
            name=strategy.name,
            description=strategy.description or "",
            parameters=parameters or {},
        )


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

    @classmethod
    def from_query_group(cls, query_group) -> "QueryTemplateDetailResponse":
        """
        QueryGroup 모델 객체로부터 QueryTemplateDetailResponse 생성

        Args:
            query_group: QueryGroup 모델 객체

        Returns:
            QueryTemplateDetailResponse 인스턴스
        """
        from ..models.query_template import binary_to_uuid

        return cls(
            queryNo=binary_to_uuid(query_group.query_group_no),
            name=query_group.name,
            isDefault=query_group.is_default,
            transformation=StrategyDetail.from_strategy(
                query_group.transformation_strategy,
                query_group.transformation_parameter
            ),
            retrieval=StrategyDetail.from_strategy(
                query_group.retrieval_strategy,
                query_group.retrieval_parameter
            ),
            reranking=StrategyDetail.from_strategy(
                query_group.reranking_strategy,
                query_group.reranking_parameter
            ),
            systemPrompt=StrategyDetail.from_strategy(
                query_group.system_prompting_strategy,
                query_group.system_prompting_parameter
            ),
            userPrompt=StrategyDetail.from_strategy(
                query_group.user_prompting_strategy,
                query_group.user_prompting_parameter
            ),
            generation=StrategyDetail.from_strategy(
                query_group.generation_strategy,
                query_group.generation_parameter
            ),
        )


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
                "isDefault": False,
                "name": "기본 Query 템플릿",
                "transformation": {
                    "no": "4b7c93a9-ca03-4caf-94e1-2ad5a4a64be1"
                },
                "retrieval": {
                    "no": "e9d321a3-98f2-4917-879b-d5407f14c44d",
                    "type": "semantic",
                    "parameters": {
                        "sematic": {
                            "threshold": 0.4,
                            "topK": 30
                        }
                    }
                },
                "reranking": {
                    "no": "ab4754a9-36b7-42b5-a0fe-64bc3de94596",
                    "parameters": {
                        "topK": 5
                    }
                },
                "systemPrompt": {
                    "no": "6bff6262-90a6-4eb1-bfc1-78bdd342c317"
                },
                "userPrompt": {
                    "no": "9c6a37bc-ef9b-4776-928c-f45c9eb65934"
                },
                "generation": {
                    "no": "bd3b754c-fd66-4a79-9cd9-3a13cebb17a1",
                    "parameters": {
                        "max_retries": 2,
                        "max_tokens": 512,
                        "temperature": 0.2,
                        "timeout": 30
                    }
                }
            }
        }
        

class QueryTemplatePartialUpdateRequest(BaseModel):
    """Query 템플릿 부분 수정 요청"""
    name: Optional[str] = Field(None, description="템플릿 이름", min_length=1, max_length=50)
    transformation: Optional[StrategyWithParameter] = Field(None, description="변환 전략")
    retrieval: Optional[StrategyWithParameter] = Field(None, description="검색 전략")
    reranking: Optional[StrategyWithParameter] = Field(None, description="재순위화 전략")
    systemPrompt: Optional[StrategyWithParameter] = Field(None, description="시스템 프롬프트 전략")
    userPrompt: Optional[StrategyWithParameter] = Field(None, description="사용자 프롬프트 전략")
    generation: Optional[StrategyWithParameter] = Field(None, description="생성 전략")
    isDefault: Optional[bool] = Field(None, description="기본 템플릿 여부")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "하이브리드 검색",
                "isDefault": True,
                "retrieval": {
                    "no": "e9d321a3-98f2-4917-879b-d5407f14c44d",
                    "parameters": {
                        "type": "semantic",
                        "semantic": {
                            "topK": 30,
                            "threshold": 0.4
                        }
                    }
                }
            }
        }
