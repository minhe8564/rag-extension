"""
Ingest 템플릿 삭제 라우터
"""
from fastapi import APIRouter, Depends, status, Response
from sqlalchemy.ext.asyncio import AsyncSession

from ....core.database import get_db
from ....core.check_role import check_role
from ....core.error_responses import admin_only_responses
from ..services.ingest import delete_ingest_template


router = APIRouter(prefix="/rag", tags=["RAG - Ingest Template Management"])


@router.delete(
    "/ingest-templates/{ingestNo}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Ingest 템플릿 삭제 (관리자 전용)",
    description="Ingest 템플릿을 삭제합니다. 관리자만 접근 가능합니다.",
    responses={
        **admin_only_responses(),
        204: {"description": "템플릿 삭제 성공 (응답 본문 없음)"},
    },
)
async def delete_ingest_template_endpoint(
    ingestNo: str,
    x_user_role: str = Depends(check_role("ADMIN")),
    session: AsyncSession = Depends(get_db),
):
    """
    Ingest 템플릿 삭제

    Args:
        ingestNo: Ingest 템플릿 ID (UUID)
        x_user_role: 사용자 역할 (헤더, 전역 security에서 자동 주입)
        session: 데이터베이스 세션

    Returns:
        204 No Content (응답 본문 없음)

    Raises:
        HTTPException 400: UUID 형식 오류
        HTTPException 404: Ingest 템플릿을 찾을 수 없음
    """
    await delete_ingest_template(
        session=session,
        ingest_no=ingestNo,
    )

    # 204 No Content는 응답 본문이 없음
    return Response(status_code=status.HTTP_204_NO_CONTENT)
