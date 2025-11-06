"""
프롬프트 삭제 라우터
"""
from fastapi import APIRouter, Depends, HTTPException, status, Header, Response
from sqlalchemy.ext.asyncio import AsyncSession

from ....core.database import get_db
from ....core.check_role import check_role
from ....core.error_responses import admin_only_responses, not_found_error_response
from ..services.prompt_delete import delete_prompt


router = APIRouter(prefix="/rag", tags=["RAG - Prompt Management"])


@router.delete(
    "/prompts/{promptNo}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="프롬프트 삭제",
    description="프롬프트를 삭제합니다. 관리자만 접근 가능합니다.",
    responses={
        **admin_only_responses(),
        404: not_found_error_response("프롬프트"),
    }
)
async def delete_prompt_endpoint(
    promptNo: str,
    x_user_role: str = Depends(check_role("ADMIN")),
    x_user_uuid: str = Header(..., alias="x-user-uuid"),
    session: AsyncSession = Depends(get_db)
):
    """
    프롬프트 삭제

    Args:
        promptNo: 프롬프트 ID (UUID)
        x_user_role: 사용자 역할 (헤더)
        x_user_uuid: 사용자 UUID (헤더)
        session: 데이터베이스 세션

    Returns:
        204 No Content

    Raises:
        HTTPException 404: 프롬프트를 찾을 수 없음
    """
    try:
        # 프롬프트 삭제
        await delete_prompt(
            session=session,
            prompt_no_str=promptNo
        )

        # 204 No Content 반환
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    except HTTPException:
        # HTTPException은 그대로 전파 (custom exception handler가 처리)
        raise

    except Exception as e:
        # 예상치 못한 오류
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"프롬프트 삭제 중 오류가 발생했습니다: {str(e)}"
        )
