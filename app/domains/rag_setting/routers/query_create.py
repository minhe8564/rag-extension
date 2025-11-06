"""
Query 템플릿 생성 라우터
"""
from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from ....core.database import get_db
from ....core.schemas import BaseResponse, Result
from ....core.check_role import check_role
from ....core.error_responses import admin_only_responses, invalid_input_error_response
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
        **admin_only_responses(),
        201: {
            "description": "Query 템플릿 생성 성공",
            "content": {
                "application/json": {
                    "example": {
                        "status": 201,
                        "code": "CREATED",
                        "message": "성공",
                        "isSuccess": True,
                        "result": {
                            "data": {
                                "queryNo": "query0001"
                            }
                        }
                    }
                }
            }
        },
        400: invalid_input_error_response(["name", "transformation", "generation.no"]),
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
        HTTPException 400: 필수 파라미터 누락 또는 전략을 찾을 수 없음
    """
    # 필수 필드 검증
    missing_fields = []
    if not request.name:
        missing_fields.append("name")
    if not request.transformation or not request.transformation.no:
        missing_fields.append("transformation.no")
    if not request.retrieval or not request.retrieval.no:
        missing_fields.append("retrieval.no")
    if not request.reranking or not request.reranking.no:
        missing_fields.append("reranking.no")
    if not request.systemPrompt or not request.systemPrompt.no:
        missing_fields.append("systemPrompt.no")
    if not request.userPrompt or not request.userPrompt.no:
        missing_fields.append("userPrompt.no")
    if not request.generation or not request.generation.no:
        missing_fields.append("generation.no")

    if missing_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "파라미터가 누락되었습니다.",
                "missing": missing_fields
            }
        )

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
        )

        # 응답 생성
        response = BaseResponse[QueryTemplateCreateResponse](
            status=201,
            code="CREATED",
            message="성공",
            isSuccess=True,
            result=Result(data=QueryTemplateCreateResponse(queryNo=query_no))
        )

        # Location 헤더 추가
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=response.model_dump(),
            headers={"Location": f"/rag/query-templates/{query_no}"}
        )

    except HTTPException as e:
        # 전략을 찾을 수 없는 경우
        if e.status_code == status.HTTP_400_BAD_REQUEST:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": e.detail,
                    "missing": []
                }
            )
        raise
