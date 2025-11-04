from typing import Dict, Any
import math
import uuid

from fastapi import APIRouter, Depends, Query, Header
from sqlalchemy.ext.asyncio import AsyncSession

from ....core.database import get_db
from ....core.schemas import BaseResponse, Result
from ....core.check_role import check_role
from ..schemas.ingest import IngestGroupListItem
from ..schemas.strategy import PaginationInfo
from ..services.ingest import list_ingest_groups


router = APIRouter(prefix="/rag", tags=["RAG - Ingest Template Management"])


def _bytes_to_uuid_str(b: bytes) -> str:
    """UUID 바이너리를 문자열로 변환"""
    try:
        return str(uuid.UUID(bytes=b))
    except Exception:
        return b.hex()


@router.get(
    "/ingest-templates",
    response_model=BaseResponse[Dict[str, Any]],
    summary="Ingest 템플릿 목록 조회 (관리자 전용)",
    description="Ingest 템플릿 목록을 조회합니다. 관리자만 접근 가능합니다.",
    responses={
        200: {"description": "성공"},
        400: {
            "description": "잘못된 요청 (유효성 검증 실패)",
            "content": {
                "application/json": {
                    "example": {
                        "status": 400,
                        "code": "VALIDATION_FAILED",
                        "message": "요청 파라미터 유효성 검증에 실패했습니다.",
                        "isSuccess": False,
                        "result": {
                            "errors": [
                                {
                                    "field": "pageNum",
                                    "message": "페이지 번호는 1 이상이어야 합니다."
                                }
                            ]
                        }
                    }
                }
            }
        },
        401: {
            "description": "인증 실패 (Access Token 없음 또는 유효하지 않음)",
            "content": {
                "application/json": {
                    "example": {
                        "status": 401,
                        "code": "INVALID_ACCESS_TOKEN",
                        "message": "엑세스 토큰이 유효하지 않거나 만료되었습니다.",
                        "isSuccess": False,
                        "result": {}
                    }
                }
            }
        },
        403: {
            "description": "권한 없음 (관리자 권한 필요)",
            "content": {
                "application/json": {
                    "example": {
                        "status": 403,
                        "code": "FORBIDDEN",
                        "message": "요청을 수행할 권한이 없습니다.",
                        "isSuccess": False,
                        "result": {
                            "requiredRole": ["ADMIN"]
                        }
                    }
                }
            }
        },
    },
)
async def get_ingest_templates(
    pageNum: int = Query(1, ge=1, description="페이지 번호"),
    pageSize: int = Query(20, ge=1, le=100, description="페이지 크기"),
    sort: str = Query("created_at", description="정렬 기준"),
    x_user_role: str = Depends(check_role("ADMIN")),
    x_user_uuid: str = Header(..., alias="x-user-uuid"),
    session: AsyncSession = Depends(get_db),
):
    """
    Ingest 템플릿 목록 조회

    Args:
        pageNum: 페이지 번호
        pageSize: 페이지 크기
        sort: 정렬 기준
        x_user_role: 사용자 역할 (헤더)
        x_user_uuid: 사용자 UUID (헤더)

    Returns:
        BaseResponse: Ingest 템플릿 목록과 페이지네이션 정보
    """
    groups, total_items = await list_ingest_groups(
        session=session,
        page_num=pageNum,
        page_size=pageSize,
        sort_by=sort,
    )

    # 응답 데이터 변환
    items = [
        IngestGroupListItem(
            ingestNo=_bytes_to_uuid_str(group.ingest_group_no),
            isDefault=group.is_default,
            extractionStrategy={
                "strategyNo": _bytes_to_uuid_str(group.extraction_strategy_no),
                "name": group.extraction_strategy.name if group.extraction_strategy else "",
                "parameter": group.extraction_parameter,
            },
            chunkingStrategy={
                "strategyNo": _bytes_to_uuid_str(group.chunking_strategy_no),
                "name": group.chunking_strategy.name if group.chunking_strategy else "",
                "parameter": group.chunking_parameter,
            },
            embeddingStrategy={
                "strategyNo": _bytes_to_uuid_str(group.embedding_strategy_no),
                "name": group.embedding_strategy.name if group.embedding_strategy else "",
                "parameter": group.embedding_parameter,
            },
        )
        for group in groups
    ]

    # 페이지네이션 정보
    total_pages = math.ceil(total_items / pageSize) if total_items > 0 else 0
    has_next = pageNum < total_pages

    pagination = PaginationInfo(
        pageNum=pageNum,
        pageSize=pageSize,
        totalItems=total_items,
        totalPages=total_pages,
        hasNext=has_next,
    )

    return BaseResponse[Dict[str, Any]](
        status=200,
        code="OK",
        message="Ingest 템플릿 목록 조회에 성공하였습니다.",
        isSuccess=True,
        result=Result(data={"data": items, "pagination": pagination}),
    )
