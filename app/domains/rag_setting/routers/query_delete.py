"""
Query 템플릿 삭제 라우터
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from ....core.database import get_db
from ....core.auth.check_role import check_role
from ..services.query import delete_query_template


router = APIRouter(prefix="/rag", tags=["RAG - Query Template Management"])


@router.delete(
    "/query-templates/{queryNo}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="[관리자] Query 템플릿 삭제",
    description="""
    Query 템플릿을 삭제합니다.
    """,
    responses={
        204: {
            "description": "Query 템플릿 삭제 성공"
        },
    },
)
async def delete_query_template_endpoint(
    queryNo: str,
    x_user_role: str = Depends(check_role("ADMIN")),
    session: AsyncSession = Depends(get_db),
):
    """
    Query 템플릿 삭제

    Args:
        queryNo: Query 템플릿 ID (UUID)
        x_user_role: 사용자 역할 (헤더, 전역 security에서 자동 주입)
        session: 데이터베이스 세션

    Returns:
        None (204 No Content)

    Raises:
        HTTPException 404: Query 템플릿을 찾을 수 없음
    """
    await delete_query_template(
        session=session,
        query_no=queryNo
    )

    # 204 No Content는 응답 본문이 없음
    return None
