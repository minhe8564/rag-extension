"""
Query 템플릿 수정 라우터
"""
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ....core.database import get_db
from ....core.schemas import BaseResponse, Result
from ....core.check_role import check_role
from ....core.error_responses import admin_only_responses
from ..schemas.query import (
    QueryTemplateUpdateRequest,
    QueryTemplateDetailResponse,
    StrategyDetail,
)
from ..services.query import update_query_template
from ..models.query_template import binary_to_uuid


router = APIRouter(prefix="/rag", tags=["RAG - Query Template Management"])


@router.put(
    "/query-templates/{queryNo}",
    response_model=BaseResponse[QueryTemplateDetailResponse],
    status_code=status.HTTP_200_OK,
    summary="Query 템플릿 수정 (관리자 전용)",
    description="Query 템플릿을 수정합니다. 관리자만 접근 가능합니다.",
    responses={
        **admin_only_responses(),
        200: {
            "description": "Query 템플릿 수정 성공",
            "content": {
                "application/json": {
                    "example": {
                        "status": 200,
                        "code": "OK",
                        "message": "성공",
                        "isSuccess": True,
                        "result": {
                            "queryNo": "f9f6b1a3-3c2e-4e2f-9b1a-9c7f3b8d2a11",
                            "name": "수정된 Query 템플릿",
                            "isDefault": False,
                            "transformation": {
                                "no": "1a7c2b6e-4d3f-45b1-98c0-6e2c4f9a7b32",
                                "name": "HyDE",
                                "description": "질문을 가상의 이상적 문서로 확장하여 검색 적합도를 높임",
                                "parameters": {}
                            },
                            "retrieval": {
                                "no": "7e3b9d12-8a41-4a1a-9c45-2f9d3a6b1c54",
                                "name": "Hybrid",
                                "description": "시맨틱 검색 + 키워드 검색 후 리랭킹",
                                "parameters": {
                                    "semantic": {"topK": 20, "threshold": 0.6}
                                }
                            },
                            "reranking": {
                                "no": "0c4d2e7a-1f9b-4e22-9b77-6a9c1d3f5e88",
                                "name": "MiniLM",
                                "description": "MiniLM 크로스 인코더",
                                "parameters": {"topK": 5}
                            },
                            "systemPrompt": {
                                "no": "b2e7c1a9-5d2f-4b3c-8a11-7f9e2c3d4a66",
                                "name": "System.GroundedAnswer",
                                "description": "출처 인용",
                                "parameters": {}
                            },
                            "userPrompt": {
                                "no": "4f1a2c3b-9d7e-4e55-8a66-1b2c3d4e5f70",
                                "name": "UserTemplate.QA",
                                "description": "사용자 질의 템플릿",
                                "parameters": {}
                            },
                            "generation": {
                                "no": "d8b7c6a5-3e2d-4c1b-9a8f-7e6d5c4b3a21",
                                "name": "ChatGPT",
                                "description": "ChatGPT 최신 모델",
                                "parameters": {
                                    "temperature": 0.3,
                                    "max_tokens": 768
                                }
                            }
                        }
                    }
                }
            }
        },
        400: {
            "description": "잘못된 요청",
            "content": {
                "application/json": {
                    "examples": {
                        "missing_fields": {
                            "summary": "필수 필드 누락",
                            "value": {
                                "status": 400,
                                "code": "VALIDATION_FAILED",
                                "message": "파라미터가 누락되었습니다.",
                                "isSuccess": False,
                                "result": {
                                    "missing": ["name", "transformation", "generation.no"]
                                }
                            }
                        },
                        "invalid_uuid": {
                            "summary": "잘못된 UUID 형식",
                            "value": {
                                "status": 400,
                                "code": "VALIDATION_FAILED",
                                "message": "올바르지 않은 Query 템플릿 ID 형식입니다.",
                                "isSuccess": False,
                                "result": {}
                            }
                        },
                        "strategy_not_found": {
                            "summary": "전략을 찾을 수 없음",
                            "value": {
                                "status": 400,
                                "code": "VALIDATION_FAILED",
                                "message": "변환 전략을 찾을 수 없습니다: xxx-xxx",
                                "isSuccess": False,
                                "result": {}
                            }
                        }
                    }
                }
            }
        },
        404: {
            "description": "Query 템플릿을 찾을 수 없음",
            "content": {
                "application/json": {
                    "example": {
                        "status": 404,
                        "code": "NOT_FOUND",
                        "message": "대상을 찾을 수 없습니다.",
                        "isSuccess": False,
                        "result": {}
                    }
                }
            }
        },
    },
)
async def update_query_template_endpoint(
    queryNo: str,
    request: QueryTemplateUpdateRequest,
    x_user_role: str = Depends(check_role("ADMIN")),
    session: AsyncSession = Depends(get_db),
):
    """
    Query 템플릿 수정

    Args:
        queryNo: Query 템플릿 ID (UUID)
        request: Query 템플릿 수정 요청
        x_user_role: 사용자 역할 (헤더, 전역 security에서 자동 주입)
        session: 데이터베이스 세션

    Returns:
        BaseResponse[QueryTemplateDetailResponse]: 수정된 Query 템플릿 상세 정보

    Raises:
        HTTPException 400: UUID 형식 오류, 전략을 찾을 수 없음
        HTTPException 404: Query 템플릿을 찾을 수 없음
    """
    try:
        # Query 템플릿 수정
        updated_query_group = await update_query_template(
            session=session,
            query_no=queryNo,
            name=request.name,
            transformation_no=request.transformation.no,
            transformation_parameters=request.transformation.parameters or {},
            retrieval_no=request.retrieval.no,
            retrieval_parameters=request.retrieval.parameters or {},
            reranking_no=request.reranking.no,
            reranking_parameters=request.reranking.parameters or {},
            system_prompt_no=request.systemPrompt.no,
            system_prompt_parameters=request.systemPrompt.parameters or {},
            user_prompt_no=request.userPrompt.no,
            user_prompt_parameters=request.userPrompt.parameters or {},
            generation_no=request.generation.no,
            generation_parameters=request.generation.parameters or {},
        )

        # 응답 데이터 생성
        detail = QueryTemplateDetailResponse(
            queryNo=binary_to_uuid(updated_query_group.query_group_no),
            name=updated_query_group.name,
            isDefault=updated_query_group.is_default,
            transformation=StrategyDetail(
                no=binary_to_uuid(updated_query_group.transformation_strategy.strategy_no),
                name=updated_query_group.transformation_strategy.name,
                description=updated_query_group.transformation_strategy.description or "",
                parameters=updated_query_group.transformation_parameter or {},
            ),
            retrieval=StrategyDetail(
                no=binary_to_uuid(updated_query_group.retrieval_strategy.strategy_no),
                name=updated_query_group.retrieval_strategy.name,
                description=updated_query_group.retrieval_strategy.description or "",
                parameters=updated_query_group.retrieval_parameter or {},
            ),
            reranking=StrategyDetail(
                no=binary_to_uuid(updated_query_group.reranking_strategy.strategy_no),
                name=updated_query_group.reranking_strategy.name,
                description=updated_query_group.reranking_strategy.description or "",
                parameters=updated_query_group.reranking_parameter or {},
            ),
            systemPrompt=StrategyDetail(
                no=binary_to_uuid(updated_query_group.system_prompting_strategy.strategy_no),
                name=updated_query_group.system_prompting_strategy.name,
                description=updated_query_group.system_prompting_strategy.description or "",
                parameters=updated_query_group.system_prompting_parameter or {},
            ),
            userPrompt=StrategyDetail(
                no=binary_to_uuid(updated_query_group.user_prompting_strategy.strategy_no),
                name=updated_query_group.user_prompting_strategy.name,
                description=updated_query_group.user_prompting_strategy.description or "",
                parameters=updated_query_group.user_prompting_parameter or {},
            ),
            generation=StrategyDetail(
                no=binary_to_uuid(updated_query_group.generation_strategy.strategy_no),
                name=updated_query_group.generation_strategy.name,
                description=updated_query_group.generation_strategy.description or "",
                parameters=updated_query_group.generation_parameter or {},
            ),
        )

        # 응답 생성
        response = BaseResponse[QueryTemplateDetailResponse](
            status=200,
            code="OK",
            message="성공",
            isSuccess=True,
            result=Result(data=detail)
        )

        return response

    except HTTPException:
        # 전역 예외 핸들러가 처리하도록 그대로 전파
        raise
