"""
프롬프트 삭제 라우터
"""
from fastapi import APIRouter, Depends, HTTPException, status, Header, Response
from sqlalchemy.ext.asyncio import AsyncSession

from ....core.database import get_db
from ....core.auth.check_role import check_role
from ..services.prompt_delete import delete_prompt


router = APIRouter(prefix="/rag", tags=["RAG - Prompt Management"])


@router.delete(
    "/prompts/{promptNo}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="[관리자] 프롬프트 삭제",
    description="프롬프트를 삭제합니다. 관리자만 접근 가능합니다.",
)
async def delete_prompt_endpoint(
    promptNo: str,
    x_user_role: str = Depends(check_role("ADMIN")),
    session: AsyncSession = Depends(get_db)
):
    """
    프롬프트 삭제

    Args:
        promptNo: 프롬프트 ID (UUID)
        x_user_role: 사용자 역할 (헤더, 전역 security에서 자동 주입)
        session: 데이터베이스 세션

    Returns:
        204 No Content

    Raises:
        HTTPException 404: 프롬프트를 찾을 수 없음
    """
    # 프롬프트 삭제
    await delete_prompt(
        session=session,
        prompt_no_str=promptNo
    )

    # 204 No Content 반환
    return Response(status_code=status.HTTP_204_NO_CONTENT)
