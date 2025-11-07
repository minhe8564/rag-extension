"""
Query 템플릿 삭제 라우터
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from ....core.database import get_db
from ....core.check_role import check_role
from ..services.query import delete_query_template


router = APIRouter(prefix="/rag", tags=["RAG - Query Template Management"])


@router.delete(
    "/query-templates/{queryNo}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Query 템플릿 삭제 (관리자 전용)",
    description="""
    Query 템플릿을 삭제합니다.

    **권한**: 관리자(ADMIN)만 접근 가능합니다.

    **Parameters**:
    - `queryNo` (path): Query 템플릿 ID (UUID 형식)

    **Response**:
    - `204 NO_CONTENT`: 삭제 성공 (응답 본문 없음)

    **Error Responses**:
    - `400 BAD_REQUEST`: UUID 형식이 올바르지 않음
    - `401 UNAUTHORIZED`: 인증 정보가 없거나 유효하지 않음
    - `403 FORBIDDEN`: 관리자 권한이 없음
    - `404 NOT_FOUND`: 대상 Query 템플릿을 찾을 수 없음
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
