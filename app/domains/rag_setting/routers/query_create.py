"""
Query 템플릿 생성 라우터
"""
from typing import Any, Dict

from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from ....core.database import get_db
from ....core.schemas import BaseResponse
from ....core.auth.check_role import check_role
from ..schemas.query import QueryTemplateCreateRequest, QueryTemplateCreateResponse
from ..services.query import create_query_template


router = APIRouter(prefix="/rag", tags=["RAG - Query Template Management"])


@router.post(
    "/query-templates",
    response_model=BaseResponse[QueryTemplateCreateResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Query 템플릿 생성 (관리자 전용)",
    description="Query 템플릿을 생성합니다. 관리자만 접근 가능합니다.",
    responses={
        201: {
            "description": "Query 템플릿 생성 성공",
            "content": {
                "application/json": {
                    "example": {
                        "status": 201,
                        "code": "CREATED",
                        "message": "Query 템플릿 생성 성공",
                        "isSuccess": True,
                        "result": {
                            "queryNo": "f1b951b3-67b3-4021-a01c-6e2e05e78823"
                        }
                    }
                }
            }
        },
    },
)
async def create_query_template_endpoint(
    request: QueryTemplateCreateRequest,
    x_user_role: str = Depends(check_role("ADMIN")),
    session: AsyncSession = Depends(get_db),
):
    """
    Query 템플릿 생성

    Args:
        request: Query 템플릿 생성 요청
        x_user_role: 사용자 역할 (헤더, 전역 security에서 자동 주입)
        session: 데이터베이스 세션

    Returns:
        BaseResponse[QueryTemplateCreateResponse]: 생성된 Query 템플릿 ID

    Raises:
        HTTPException 400: 전략을 찾을 수 없음
    """
    try:
        # Query 템플릿 생성
        query_no = await create_query_template(
            session=session,
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
            is_default=request.isDefault,
        )

        # 응답 생성
        response = BaseResponse[Dict[str, Any]](
            status=201,
            code="CREATED",
            message="Query 템플릿 생성에 성공하였습니다.",
            isSuccess=True,
            result={"queryNo": query_no}
        )

        # Location 헤더 추가
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=response.model_dump(),
            headers={"Location": f"/rag/query-templates/{query_no}"}
        )

    except HTTPException:
        # 전역 예외 핸들러가 처리하도록 그대로 전파
        raise
