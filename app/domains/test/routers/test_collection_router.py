from __future__ import annotations

import uuid
from typing import Dict, Any, List
from math import ceil
from datetime import datetime

from fastapi import APIRouter, Request, HTTPException, status, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ....core.database import get_db
from ....core.check_role import check_role
from ....core.schemas import BaseResponse, Pagination
from ..schemas.response.test_collection import TestCollectionListItem
from ..schemas.response.test_file import TestFileListItem
from ..services.test_collection import list_test_collections, count_test_collections
from ...collection.services.collections import list_files_in_collection as list_files_in_collection_service
from ..services.test_file import list_test_files, count_test_files
from ....core.cursor import CursorParams, get_cursor_params


router = APIRouter(prefix="/test", tags=["Test"])

@router.get(
    "/collections",
    response_model=BaseResponse[List[TestCollectionListItem]],
    summary="Test Collection 목록 조회 (관리자)",
    description="Test Collection 목록을 조회합니다. 관리자 전용.",
    response_model_exclude_none=True
)
async def get_test_collections(
    request: Request,
    session: AsyncSession = Depends(get_db),
    x_user_role: str = Depends(check_role("ADMIN")),
    pageSize: int = Query(5, ge=1, le=100, description="페이지 크기"),
    cursor: CursorParams = Depends(get_cursor_params)
):
    # 헤더에서 사용자 UUID만 확인 (Role은 check_role 의존성이 검사)
    x_user_uuid = request.headers.get("x-user-uuid")
    if not x_user_uuid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="x-user-uuid header required",
        )

    limit = pageSize

    # limit+1로 조회해서 hasNext 판단
    items = await list_test_collections(
        session=session,
        limit=limit + 1,
        cursor_created_at=cursor.cursorCreatedAt,
        cursor_id=cursor.cursorId,
    )

    has_next = len(items) > limit
    if has_next:
        next_candidate = items[limit - 1]
        next_cursor = {
            "cursorCreatedAt": next_candidate.createdAt,
            "cursorId": next_candidate.testCollectionNo,
        }
        items = items[:limit]
    else:
        next_cursor = None

    return BaseResponse[List[TestCollectionListItem]](
        status=200,
        code="OK",
        message="조회 성공",
        isSuccess=True,
        result={
            "data": items,
            "hasNext": has_next,
            "nextCursor": next_cursor,
        },
    )


@router.get(
    "/collections/{test_collection_no}/files",
    response_model=BaseResponse[List[TestFileListItem]],
    summary="Test Collection 문서 목록 조회",
    description="Test Collection 내 문서 목록을 페이지네이션하여 조회합니다.",
)
async def get_test_collection_files(
    test_collection_no: str,
    request: Request,
    session: AsyncSession = Depends(get_db),
    x_user_role: str = Depends(check_role("ADMIN")),
    pageNum: int = Query(1, ge=1, description="페이지 번호"),
    pageSize: int = Query(5, ge=1, le=100, description="페이지 크기"),
):
    # 사용자 UUID 헤더 확인 (Role은 check_role 종속성에서 검사됨)
    x_user_uuid = request.headers.get("x-user-uuid")
    if not x_user_uuid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="x-user-uuid header required")
    
    limit = pageSize
    offset = (pageNum - 1) * pageSize

    total_items = await count_test_files(session=session, test_collection_no=test_collection_no)
    rows: List[TestFileListItem] = await list_test_files(
        session=session,
        limit=limit,
        offset=offset,
        test_collection_no=test_collection_no,
    )

    total_pages = ceil(total_items / pageSize) if total_items > 0 else 1
    has_next = pageNum < total_pages

    return BaseResponse[List[TestFileListItem]](
        status=200,
        code="OK",
        message="조회 성공",
        isSuccess=True,
        result={
            "data": rows,
            "pagination": Pagination(
                pageNum=pageNum,
                pageSize=pageSize,
                totalItems=total_items,
                totalPages=total_pages,
                hasNext=has_next,
            )
        },
    )
