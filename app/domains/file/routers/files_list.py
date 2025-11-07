from __future__ import annotations

from fastapi import APIRouter, Depends, Header, Request, HTTPException, status, Query
from typing import Dict, Any, List
import math
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.schemas import BaseResponse, Pagination
from ..schemas.response.files import FileListItem
from ..services import files as files_service


router = APIRouter(prefix="/files", tags=["File"])


@router.get("", response_model=BaseResponse[List[FileListItem]])
async def list_my_files(
    pageNum: int = Query(1, ge=1, description="페이지 번호"),
    pageSize: int = Query(5, ge=1, le=100, description="페이지 크기"),
    category: str | None = None,
    session: AsyncSession = Depends(get_db),
    http_request: Request = None,
):
    if http_request is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Request context unavailable")
    x_user_role = http_request.headers.get("x-user-role")
    x_user_uuid = http_request.headers.get("x-user-uuid")
    if not x_user_role or not x_user_uuid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="x-user-role/x-user-uuid headers required")

    # Calculate pagination from pageNum/pageSize
    limit = pageSize
    offset = (pageNum - 1) * pageSize

    items, total_items = await files_service.list_files_by_offer(
        session,
        user_no=x_user_uuid,
        limit=limit,
        offset=offset,
        category_no=category,
    )

    total_pages = math.ceil(total_items / pageSize) if total_items > 0 else 0
    has_next = pageNum < total_pages

    # Include pagination info in response (wrap both under result.data)
    return BaseResponse[List[FileListItem]](
        status=200,
        code="OK",
        message="문서 목록 조회에 성공했습니다.",
        isSuccess=True,
        result={
            "data": items,
            "pagination": Pagination(
                    pageNum=pageNum,
                    pageSize=pageSize,
                    totalItems=total_items,
                    totalPages=total_pages,
                    hasNext=has_next,
            ),
        },
    )
