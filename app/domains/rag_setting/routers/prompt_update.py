"""
프롬프트 수정 라우터
"""
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession

from ....core.database import get_db
from ....core.schemas import BaseResponse, Result
from ....core.check_role import check_role
from ....core.error_responses import (
    admin_only_responses,
    not_found_error_response,
    conflict_error_response,
    invalid_input_error_response
)
from ..schemas.prompt import PromptUpdateRequest
from ..services.prompt_update import update_prompt


router = APIRouter(prefix="/rag", tags=["RAG - Prompt Management"])


@router.put(
    "/prompts/{promptNo}",
    response_model=BaseResponse[Dict[str, Any]],
    summary="프롬프트 수정",
    description="프롬프트를 수정합니다. 관리자만 접근 가능합니다.",
    responses={
        **admin_only_responses(),
        400: invalid_input_error_response(["name", "content"]),
        404: not_found_error_response("프롬프트"),
        409: conflict_error_response("프롬프트"),
    }
)
async def update_prompt_endpoint(
    promptNo: str,
    request: PromptUpdateRequest,
    x_user_role: str = Depends(check_role("ADMIN")),
    x_user_uuid: str = Header(..., alias="x-user-uuid"),
    session: AsyncSession = Depends(get_db)
):
    """
    프롬프트 수정

    Args:
        promptNo: 프롬프트 ID (UUID)
        request: 프롬프트 수정 요청 데이터
        x_user_role: 사용자 역할 (헤더)
        x_user_uuid: 사용자 UUID (헤더)
        session: 데이터베이스 세션

    Returns:
        BaseResponse: 수정 성공 응답

    Raises:
        HTTPException 400: 필수 파라미터 누락 또는 유효성 검증 실패
        HTTPException 404: 프롬프트를 찾을 수 없음
        HTTPException 409: 동일한 이름의 프롬프트 존재
    """
    try:
        # 프롬프트 수정
        await update_prompt(
            session=session,
            prompt_no_str=promptNo,
            name=request.name,
            content=request.content
        )

        # 응답 반환
        return BaseResponse[Dict[str, Any]](
            status=200,
            code="OK",
            message="성공",
            isSuccess=True,
            result=Result(data={})
        )

    except HTTPException:
        # HTTPException은 그대로 전파 (custom exception handler가 처리)
        raise

    except Exception as e:
        # 예상치 못한 오류
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"프롬프트 수정 중 오류가 발생했습니다: {str(e)}"
        )
