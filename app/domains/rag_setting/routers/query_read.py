"""
Query 템플릿 조회 라우터 (목록 + 상세)
"""
from typing import Dict, Any

from fastapi import APIRouter, Depends, status, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ....core.database import get_db
from ....core.schemas import BaseResponse, Result
from ....core.auth.check_role import check_role
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
                        "message": "Query 템플릿 목록 조회 성공",
                        "isSuccess": True,
                        "result": {
                            "data": [
                            {
                                "queryNo": "2043a2c8-bc99-11f0-a5ea-0e6c5c03bab1",
                                "name": "하이브리드 검색",
                                "isDefault": False
                            },
                            {
                                "queryNo": "f1b951b3-67b3-4021-a01c-6e2e05e78823",
                                "name": "기본 Query 템플릿",
                                "isDefault": True
                            },
                            ],
                            "pagination": {
                            "pageNum": 1,
                            "pageSize": 20,
                            "totalItems": 2,
                            "totalPages": 1,
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
        message="Query 템플릿 목록 조회 성공",
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
                        "message": "Query 템플릿 상세 조회 성공",
                        "isSuccess": True,
                        "result": {
                            "queryNo": "466cf479-bc99-11f0-a5ea-0e6c5c03bab1",
                            "name": "ChatGPT",
                            "isDefault": False,
                            "transformation": {
                                "no": "4b7c93a9-ca03-4caf-94e1-2ad5a4a64be1",
                                "code": "TRF_BUFFER",
                                "name": "Buffer",
                                "description": "변환없이 다음 단계로 전달",
                                "parameters": {
                                    "type": "buffer"
                                }
                            },
                            "retrieval": {
                            "no": "e9d321a3-98f2-4917-879b-d5407f14c44d",
                            "code": "RET_SEMANTIC",
                            "name": "시맨틱 검색",
                            "description": "시맨틱 검색",
                            "parameters": {
                                "type": "semantic",
                                "sematic": {
                                    "topK": 30,
                                    "threshold": 0.4
                                }
                            }
                            },
                            "reranking": {
                            "no": "ab4754a9-36b7-42b5-a0fe-64bc3de94596",
                            "code": "RER",
                            "name": "MiniLM",
                            "description": "MiniLM 크로스 재정렬기",
                            "parameters": {
                                "topK": 5,
                                "model": "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"
                            }
                            },
                            "systemPrompt": {
                            "no": "6bff6262-90a6-4eb1-bfc1-78bdd342c317",
                            "code": "PMT_SYSTEM",
                            "name": "샘플 시스템 프롬프트",
                            "description": "샘플 시스템 프롬프트",
                            "parameters": {
                                "type": "system",
                                "content": "당신은 유용한 RAG 어시스턴트입니다. 사용자의 언어(기본: 한국어)로 간결하게 답하고, 정확성을 최우선으로 하며, 모든 주장은 검색·조회된 출처에 근거해 제시하세요."
                            }
                            },
                            "userPrompt": {
                            "no": "9c6a37bc-ef9b-4776-928c-f45c9eb65934",
                            "code": "PMT_USER",
                            "name": "샘플 사용자 프롬프트",
                            "description": "샘플 사용자 프롬프트",
                            "parameters": {
                                "type": "user",
                                "content": "다음 지침을 따라 한국어로 간결하게 답하세요: (1) 아래 참고문서에서 근거를 먼저 찾고, (2) 문서 내용에 한해 답변하세요.\n질문: {{query}}\n참고문서: {{docs}}"
                            }
                            },
                            "generation": {
                            "no": "b3f8bd78-520b-4e2e-b516-786f45fbe83a",
                            "code": "GEN_OPENAI",
                            "name": "gpt-4o",
                            "description": "OpenAI의 텍스트 생성 모델",
                            "parameters": {
                                "model": "gpt-4o",
                                "timeout": 30,
                                "provider": "openai",
                                "max_tokens": 512,
                                "max_retries": 2,
                                "temperature": 0.2
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
            code=query_group.transformation_strategy.code,
            name=query_group.transformation_strategy.name,
            description=query_group.transformation_strategy.description or "",
            parameters=query_group.transformation_parameter or {},
        ),
        retrieval=StrategyDetail(
            no=binary_to_uuid(query_group.retrieval_strategy.strategy_no),
            code=query_group.retrieval_strategy.code,
            name=query_group.retrieval_strategy.name,
            description=query_group.retrieval_strategy.description or "",
            parameters=query_group.retrieval_parameter or {},
        ),
        reranking=StrategyDetail(
            no=binary_to_uuid(query_group.reranking_strategy.strategy_no),
            code=query_group.reranking_strategy.code,
            name=query_group.reranking_strategy.name,
            description=query_group.reranking_strategy.description or "",
            parameters=query_group.reranking_parameter or {},
        ),
        systemPrompt=StrategyDetail(
            no=binary_to_uuid(query_group.system_prompting_strategy.strategy_no),
            code=query_group.system_prompting_strategy.code,
            name=query_group.system_prompting_strategy.name,
            description=query_group.system_prompting_strategy.description or "",
            parameters=query_group.system_prompting_parameter or {},
        ),
        userPrompt=StrategyDetail(
            no=binary_to_uuid(query_group.user_prompting_strategy.strategy_no),
            code=query_group.user_prompting_strategy.code,
            name=query_group.user_prompting_strategy.name,
            description=query_group.user_prompting_strategy.description or "",
            parameters=query_group.user_prompting_parameter or {},
        ),
        generation=StrategyDetail(
            no=binary_to_uuid(query_group.generation_strategy.strategy_no),
            code=query_group.generation_strategy.code,
            name=query_group.generation_strategy.name,
            description=query_group.generation_strategy.description or "",
            parameters=query_group.generation_parameter or {},
        ),
    )

    # 응답 생성
    response = BaseResponse[QueryTemplateDetailResponse](
        status=200,
        code="OK",
        message="Query 템플릿 상세 조회 성공",
        isSuccess=True,
        result=Result(data=detail)
    )

    return response
