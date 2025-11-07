"""
Query 템플릿 조회 라우터 (목록 + 상세)
"""
from typing import Dict, Any

from fastapi import APIRouter, Depends, status, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ....core.database import get_db
from ....core.schemas import BaseResponse, Result
from ....core.check_role import check_role
from ..schemas.query import (
    QueryTemplateListItem,
    QueryTemplateDetailResponse,
    StrategyDetail,
)
from ..schemas.strategy import PaginationInfo
from ..services.query import list_query_templates, get_query_template
from ..models.query_template import binary_to_uuid


router = APIRouter(prefix="/rag", tags=["RAG - Query Template Management"])

# 페이지네이션 설정
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100


@router.get(
    "/query-templates",
    response_model=BaseResponse[Dict[str, Any]],
    status_code=status.HTTP_200_OK,
    summary="Query 템플릿 목록 조회 (관리자 전용)",
    description="Query 템플릿 목록을 조회합니다. 관리자만 접근 가능합니다.",
    responses={
        200: {
            "description": "Query 템플릿 목록 조회 성공",
            "content": {
                "application/json": {
                    "example": {
                        "status": 200,
                        "code": "SUCCESS",
                        "message": "성공",
                        "isSuccess": True,
                        "result": {
                            "data": [
                                {
                                    "queryNo": "56511d54-b561-4a7c-9e0c-4bd1d0961ac8",
                                    "name": "기본 Query 템플릿",
                                    "isDefault": True
                                },
                                {
                                    "queryNo": "56511d54-b561-4a7c-9e0c-4bd1d0961ac8",
                                    "name": "확장된 Query 템플릿",
                                    "isDefault": False
                                }
                            ],
                            "pagination": {
                                "totalItems": 2,
                                "totalPages": 1,
                                "currentPage": 1,
                                "pageSize": 20,
                                "hasNext": False
                            }
                        }
                    }
                }
            }
        },
    },
)
async def list_query_templates_endpoint(
    pageNum: int = Query(1, ge=1, description="페이지 번호"),
    pageSize: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE, description="페이지 크기 (최대 100)"),
    sort: str = Query("name", description="정렬 기준 (name, created_at)"),
    x_user_role: str = Depends(check_role("ADMIN")),
    session: AsyncSession = Depends(get_db),
):
    """
    Query 템플릿 목록 조회

    Args:
        pageNum: 페이지 번호 (기본값: 1)
        pageSize: 페이지 크기 (기본값: 20, 최대값: 100)
        x_user_role: 사용자 역할 (헤더, 전역 security에서 자동 주입)
        session: 데이터베이스 세션

    Returns:
        BaseResponse[Dict[str, Any]]: Query 템플릿 목록 및 페이지네이션 정보
    """

    # Get query templates
    query_templates, total_items = await list_query_templates(
        session=session,
        page_num=pageNum,
        page_size=pageSize,
        sort_by="name",
    )

    # Transform to response schema
    data = [
        QueryTemplateListItem(
            queryNo=binary_to_uuid(template.query_group_no),
            name=template.name,
            isDefault=template.is_default,
        )
        for template in query_templates
    ]

    # Calculate pagination info
    total_pages = (total_items + pageSize - 1) // pageSize if total_items > 0 else 0
    has_next = pageNum < total_pages

    pagination = PaginationInfo(
        pageNum=pageNum,
        pageSize=pageSize,
        totalItems=total_items,
        totalPages=total_pages,
        hasNext=has_next,
    )

    # Create response
    response = BaseResponse[Dict[str, Any]](
        status=200,
        code="SUCCESS",
        message="Query 템플릿 목록 조회에 성공하였습니다.",
        isSuccess=True,
        result={
                "data": [item.model_dump() for item in data],
                "pagination": pagination.model_dump(),
            }
    )
    

    return response


@router.get(
    "/query-templates/{queryNo}",
    response_model=BaseResponse[QueryTemplateDetailResponse],
    status_code=status.HTTP_200_OK,
    summary="Query 템플릿 상세 조회 (관리자 전용)",
    description="Query 템플릿 상세 정보를 조회합니다. 관리자만 접근 가능합니다.",
    responses={
        200: {
            "description": "Query 템플릿 상세 조회 성공",
            "content": {
                "application/json": {
                    "example": {
                        "status": 200,
                        "code": "OK",
                        "message": "성공",
                        "isSuccess": True,
                        "result": {
                            "queryNo": "f9f6b1a3-3c2e-4e2f-9b1a-9c7f3b8d2a11",
                            "name": "기본 QUERY 템플릿",
                            "isDefault": True,
                            "transformation": {
                                "no": "1a7c2b6e-4d3f-45b1-98c0-6e2c4f9a7b32",
                                "name": "HyDE",
                                "description": "질문을 가상의 이상적 문서로 확장하여 검색 적합도를 높임",
                                "parameters": { "code": "HyDE" }
                            },
                            "retrieval": {
                                "no": "7e3b9d12-8a41-4a1a-9c45-2f9d3a6b1c54",
                                "name": "Hybrid",
                                "description": "시맨틱 검색 + 키워드 검색 후 리랭킹",
                                "parameters": {
                                    "code": "Hybrid",
                                    "semantic": {"top_k": 20, "threshold": 0.6},
                                    "keyword": {"top_k": 20},
                                    "reranker": {"type": "weighted", "weight": 0.4, "top_k": 10}
                                }
                            },
                            "reranking": {
                                "no": "0c4d2e7a-1f9b-4e22-9b77-6a9c1d3f5e88",
                                "name": "MiniLM",
                                "description": "MiniLM 크로스 인코더(pointwise 방식)로 취합",
                                "parameters": {
                                    "model": "cross-encoder/ms-marco-MiniLM-L6-v2",
                                    "top_k": 5
                                }
                            },
                            "systemPrompt": {
                                "no": "b2e7c1a9-5d2f-4b3c-8a11-7f9e2c3d4a66",
                                "name": "기본 시스템 프롬프트",
                                "description": "기본 시스템 프롬프트",
                                "parameters": {
                                    "content": "당신은 유용한 RAG 어시스턴트입니다. 사용자의 언어(기본: 한국어)로 간결하게 답하고, 정확성을 최우선으로 하며, 모든 주장은 검색·조회된 출처에 근거해 제시하세요."
                                }
                            },
                            "userPrompt": {
                                "no": "4f1a2c3b-9d7e-4e55-8a66-1b2c3d4e5f70",
                                "name": "기본 사용자 프롬프트",
                                "description": "기본 사용자 프롬프트",
                                "parameters": {
                                    "content": "다음 지침을 따라 한국어로 간결하게 답하세요: (1) 아래 참고문서에서 근거를 먼저 찾고, (2) 문서 내용에 한해 답변하세요.\n질문: {{user_query}}\n참고문서: {{docs}}"
                                }
                            },
                            "generation": {
                                "no": "d8b7c6a5-3e2d-4c1b-9a8f-7e6d5c4b3a21",
                                "name": "qwen3-vl:8b",
                                "description": "알리바바 최신 텍스트 생성 모델",
                                "parameters": {
                                    "model": "qwen3-vl:8b",
                                    "provider": "ollama",
                                    "temperature": 0.3,
                                    "timeout": 100,
                                    "maxRetries": 5,
                                    "max_tokens": 768,
                                }
                            }
                        }
                    }
                }
            }
        },
    },
)
async def get_query_template_endpoint(
    queryNo: str,
    x_user_role: str = Depends(check_role("ADMIN")),
    session: AsyncSession = Depends(get_db),
):
    """
    Query 템플릿 상세 조회

    Args:
        queryNo: Query 템플릿 ID (UUID)
        x_user_role: 사용자 역할 (헤더, 전역 security에서 자동 주입)
        session: 데이터베이스 세션

    Returns:
        BaseResponse[QueryTemplateDetailResponse]: Query 템플릿 상세 정보

    Raises:
        HTTPException 400: UUID 형식 오류
        HTTPException 404: Query 템플릿을 찾을 수 없음
    """
    # Query 템플릿 조회
    query_group = await get_query_template(session=session, query_no=queryNo)

    # 응답 데이터 생성
    detail = QueryTemplateDetailResponse(
        queryNo=binary_to_uuid(query_group.query_group_no),
        name=query_group.name,
        isDefault=query_group.is_default,
        transformation=StrategyDetail(
            no=binary_to_uuid(query_group.transformation_strategy.strategy_no),
            name=query_group.transformation_strategy.name,
            description=query_group.transformation_strategy.description or "",
            parameters=query_group.transformation_parameter or {},
        ),
        retrieval=StrategyDetail(
            no=binary_to_uuid(query_group.retrieval_strategy.strategy_no),
            name=query_group.retrieval_strategy.name,
            description=query_group.retrieval_strategy.description or "",
            parameters=query_group.retrieval_parameter or {},
        ),
        reranking=StrategyDetail(
            no=binary_to_uuid(query_group.reranking_strategy.strategy_no),
            name=query_group.reranking_strategy.name,
            description=query_group.reranking_strategy.description or "",
            parameters=query_group.reranking_parameter or {},
        ),
        systemPrompt=StrategyDetail(
            no=binary_to_uuid(query_group.system_prompting_strategy.strategy_no),
            name=query_group.system_prompting_strategy.name,
            description=query_group.system_prompting_strategy.description or "",
            parameters=query_group.system_prompting_parameter or {},
        ),
        userPrompt=StrategyDetail(
            no=binary_to_uuid(query_group.user_prompting_strategy.strategy_no),
            name=query_group.user_prompting_strategy.name,
            description=query_group.user_prompting_strategy.description or "",
            parameters=query_group.user_prompting_parameter or {},
        ),
        generation=StrategyDetail(
            no=binary_to_uuid(query_group.generation_strategy.strategy_no),
            name=query_group.generation_strategy.name,
            description=query_group.generation_strategy.description or "",
            parameters=query_group.generation_parameter or {},
        ),
    )

    # 응답 생성
    response = BaseResponse[Dict[str, Any]](
        status=200,
        code="OK",
        message="Query 템플릿 상세 조회에 성공하였습니다.",
        isSuccess=True,
        result=detail
    )

    return response
