"""
프롬프트 수정 라우터
"""
from typing import Dict, Any
import uuid

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
from ..schemas.prompt import PromptUpdateRequest, PromptDetailResponse
from ..services.prompt_update import update_prompt


router = APIRouter(prefix="/rag", tags=["RAG - Prompt Management"])


@router.put(
    "/prompts/{promptNo}",
    response_model=BaseResponse[PromptDetailResponse],
    summary="프롬프트 수정",
    description="프롬프트를 수정합니다. 관리자만 접근 가능합니다.",
    responses={
        **admin_only_responses(),
        400: invalid_input_error_response(["name", "description", "content"]),
        404: not_found_error_response("프롬프트"),
        409: conflict_error_response("프롬프트"),
    }
)
async def update_prompt_endpoint(
    promptNo: str,
    request: PromptUpdateRequest,
    x_user_role: str = Depends(check_role("ADMIN")),
    session: AsyncSession = Depends(get_db)
):
    """
    프롬프트 수정

    Args:
        promptNo: 프롬프트 ID (UUID)
        request: 프롬프트 수정 요청 데이터
        x_user_role: 사용자 역할 (헤더, 전역 security에서 자동 주입)
        session: 데이터베이스 세션

    Returns:
        BaseResponse[PromptDetailResponse]: 수정된 프롬프트 정보

    Raises:
        HTTPException 400: 필수 파라미터 누락 또는 유효성 검증 실패
        HTTPException 404: 프롬프트를 찾을 수 없음
        HTTPException 409: 동일한 이름의 프롬프트 존재
    """
    # 프롬프트 수정
    updated_prompt = await update_prompt(
        session=session,
        prompt_no_str=promptNo,
        name=request.name,
        description=request.description,
        content=request.content
    )

    # 수정된 프롬프트 정보 반환
    return BaseResponse[PromptDetailResponse](
        status=200,
        code="OK",
        message="프롬프트 수정에 성공하였습니다.",
        isSuccess=True,
        result=Result(data=PromptDetailResponse(
            promptNo=str(uuid.UUID(bytes=updated_prompt.strategy_no)),
            name=updated_prompt.name,
            type=updated_prompt.parameter.get("type", "system") if updated_prompt.parameter else "system",
            description=updated_prompt.description,
            content=updated_prompt.parameter.get("content", "") if updated_prompt.parameter else ""
        ))
    )
