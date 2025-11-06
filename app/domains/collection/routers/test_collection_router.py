from __future__ import annotations

import uuid
from typing import List

from fastapi import APIRouter, Request, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ....core.database import get_db
from ....core.check_role import check_role
from ....core.schemas import BaseResponse, Result
from ..schemas.response.test_collection import TestCollectionListItem
from ..services.test_collection import list_test_collections


router = APIRouter(prefix="/rag", tags=["Collection - Test"])


def _bytes_to_uuid_str(b: bytes) -> str:
    try:
        return str(uuid.UUID(bytes=b))
    except Exception:
        return b.hex()


@router.get(
    "/test-collections",
    response_model=BaseResponse[List[TestCollectionListItem]],
    summary="Test Collection 목록 조회 (관리자)",
    description="Test Collection 목록을 조회합니다. 관리자 전용.",
)
async def get_test_collections(
    request: Request,
    session: AsyncSession = Depends(get_db),
    x_user_role: str = Depends(check_role("ADMIN")),
    limit: int = 20,
    offset: int = 0,
):
    # 헤더에서 사용자 UUID만 확인 (Role은 check_role 의존성이 검사)
    x_user_uuid = request.headers.get("x-user-uuid")
    if not x_user_uuid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="x-user-uuid header required")

    rows = await list_test_collections(
        session=session,
        limit=limit,
        offset=offset,
    )

    items = [
        TestCollectionListItem(
            testCollectionNo=_bytes_to_uuid_str(row.test_collection_no),
            name=row.name,
            ingestNo=_bytes_to_uuid_str(row.ingest_group_no),
            createdAt=row.created_at,
        )
        for row in rows
    ]

    return BaseResponse[List[TestCollectionListItem]](
        status=200,
        code="OK",
        message="조회 성공",
        isSuccess=True,
        result=Result(data=items),
    )
