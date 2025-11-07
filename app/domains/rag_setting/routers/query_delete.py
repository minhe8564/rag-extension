"""
Query 템플릿 삭제 라우터
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from ....core.database import get_db
from ....core.check_role import check_role
from ....core.error_responses import admin_only_responses
from ..services.query import delete_query_template


router = APIRouter(prefix="/rag", tags=["RAG - Query Template Management"])


@router.delete(
    "/query-templates/{queryNo}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Query 템플릿 삭제 (관리자 전용)",
    description="""
    Query 템플릿을 삭제합니다.
    """,
    responses={
        **admin_only_responses(),
        204: {
            "description": "Query 템플릿 삭제 성공 (응답 본문 없음)"
        },
        400: {
            "description": "요청 파라미터 검증 실패",
            "content": {
                "application/json": {
                    "example": {
                        "status": 400,
                        "code": "VALIDATION_FAILED",
                        "message": "올바르지 않은 Query 템플릿 ID 형식입니다.",
                        "isSuccess": False,
                        "result": {}
                    }
                }
            }
        },
        404: {
            "description": "Query 템플릿을 찾을 수 없음",
            "content": {
                "application/json": {
                    "example": {
                        "status": 404,
                        "code": "NOT_FOUND",
                        "message": "대상을 찾을 수 없습니다.",
                        "isSuccess": False,
                        "result": {}
                    }
                }
            }
        }
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
        HTTPException 400: UUID 형식 오류
        HTTPException 404: Query 템플릿을 찾을 수 없음
    """
    await delete_query_template(
        session=session,
        query_no=queryNo
    )

    # 204 No Content는 응답 본문이 없음
    return None
