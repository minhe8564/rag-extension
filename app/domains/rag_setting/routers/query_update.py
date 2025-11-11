"""
Query 템플릿 수정 라우터
"""
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ....core.database import get_db
from ....core.schemas import BaseResponse, Result
from ....core.auth.check_role import check_role
from ..schemas.query import (
    QueryTemplateUpdateRequest,
    QueryTemplatePartialUpdateRequest,
    QueryTemplateDetailResponse,
)
from ..services.query import update_query_template, partial_update_query_template


router = APIRouter(prefix="/rag", tags=["RAG - Query Template Management"])


# @router.put(
#     "/query-templates/{queryNo}",
#     response_model=BaseResponse[QueryTemplateDetailResponse],
#     status_code=status.HTTP_200_OK,
#     summary="Query 템플릿 수정 (관리자 전용)",
#     description="Query 템플릿을 수정합니다. 관리자만 접근 가능합니다.",
#     responses={
#         200: {
#             "description": "Query 템플릿 수정 성공",
#             "content": {
#                 "application/json": {
#                     "example": {
#                         "status": 200,
#                         "code": "OK",
#                         "message": "성공",
#                         "isSuccess": True,
#                         "result": {}
#                     }
#                 }
#             }
#         },
#     },
# )
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
            is_default=request.isDefault if hasattr(request, 'isDefault') else None,
        )

        # 수정된 결과를 응답 스키마로 변환 (스키마 메서드 사용)
        detail = QueryTemplateDetailResponse.from_query_group(updated_query_group)

        # 응답 생성
        response = BaseResponse[QueryTemplateDetailResponse](
            status=200,
            code="OK",
            message="Query 템플릿 수정에 성공하였습니다.",
            isSuccess=True,
            result=Result(data=detail)
        )

        return response

    except HTTPException:
        # 전역 예외 핸들러가 처리하도록 그대로 전파
        raise


@router.put(
    "/query-templates/{queryNo}",
    response_model=BaseResponse[QueryTemplateDetailResponse],
    status_code=status.HTTP_200_OK,
    summary="Query 템플릿 부분 수정 (관리자 전용)",
    description="Query 템플릿의 일부 필드를 수정합니다. 관리자만 접근 가능합니다.",
    responses={
        200: {  
            "description": "Query 템플릿 부분 수정 성공",
            "content": {
                "application/json": {
                    "example": {
                        "status": 200,
                        "code": "OK",
                        "message": "성공",
                        "isSuccess": True,
                        "result": {}
                    }
                }
            }
        },
    },
)
async def partial_update_query_template_endpoint(
    queryNo: str,
    request: QueryTemplatePartialUpdateRequest,
    x_user_role: str = Depends(check_role("ADMIN")),
    session: AsyncSession = Depends(get_db),
):
    """
    Query 템플릿 부분 수정

    Args:
        queryNo: Query 템플릿 ID (UUID)
        request: Query 템플릿 부분 수정 요청
        x_user_role: 사용자 역할 (헤더, 전역 security에서 자동 주입)
        session: 데이터베이스 세션

    Returns:
        BaseResponse[QueryTemplateDetailResponse]: 수정된 Query 템플릿 상세 정보

    Raises:
        HTTPException 400: 수정할 필드가 없음, UUID 형식 오류, 전략을 찾을 수 없음
        HTTPException 404: Query 템플릿을 찾을 수 없음
    """
    if not request.model_dump(exclude_none=True):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="수정할 필드를 입력해주세요.",
        )

    try:
        await partial_update_query_template(
            session=session,
            query_no=queryNo,
            name=request.name,
            transformation_no=request.transformation.no if request.transformation else None,
            transformation_parameters=(
                request.transformation.parameters if request.transformation else None
            ),
            retrieval_no=request.retrieval.no if request.retrieval else None,
            retrieval_parameters=(
                request.retrieval.parameters if request.retrieval else None
            ),
            reranking_no=request.reranking.no if request.reranking else None,
            reranking_parameters=(
                request.reranking.parameters if request.reranking else None
            ),
            system_prompt_no=request.systemPrompt.no if request.systemPrompt else None,
            system_prompt_parameters=(
                request.systemPrompt.parameters if request.systemPrompt else None
            ),
            user_prompt_no=request.userPrompt.no if request.userPrompt else None,
            user_prompt_parameters=(
                request.userPrompt.parameters if request.userPrompt else None
            ),
            generation_no=request.generation.no if request.generation else None,
            generation_parameters=(
                request.generation.parameters if request.generation else None
            ),
            is_default=request.isDefault,
        )

        response = BaseResponse[QueryTemplateDetailResponse](
            status=200,
            code="OK",
            message="성공",
            isSuccess=True,
            result={}
        )

        return response

    except HTTPException:
        raise
