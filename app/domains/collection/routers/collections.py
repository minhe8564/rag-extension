from __future__ import annotations

from typing import List, Dict, Any
import math

from fastapi import APIRouter, Depends, HTTPException, Request, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.schemas import BaseResponse, Pagination
from ..schemas.response.collection import CollectionListItem
from ..services.collections import list_collections_by_offer as list_collections_service
from ..services.collections import list_files_in_collection as list_files_in_collection_service
from app.domains.file.schemas.response.files import FileListItem


router = APIRouter(prefix="/collections", tags=["Collection"])


@router.get("/{collection_no}/files", response_model=BaseResponse[Dict[str, Any]])
async def list_collection_files(
    collection_no: str,
    pageNum: int = Query(1, ge=1, description="페이지 번호"),
    pageSize: int = Query(5, ge=1, le=100, description="페이지 크기"),
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

    items, total_items = await list_files_in_collection_service(
        session,
        user_no=x_user_uuid,
        collection_no=collection_no,
        limit=limit,
        offset=offset,
    )

    total_pages = math.ceil(total_items / pageSize) if total_items > 0 else 0
    has_next = pageNum < total_pages

    return BaseResponse[Dict[str, Any]](
        status=200,
        code="OK",
        message="컬렉션 조회 성공",
        isSuccess=True,
        result={
            "data": {
                "data": items,
                "pagination": Pagination(
                    pageNum=pageNum,
                    pageSize=pageSize,
                    totalItems=total_items,
                    totalPages=total_pages,
                    hasNext=has_next,
                ),
            }
        },
    )


@router.get("", response_model=BaseResponse[Dict[str, Any]])
async def list_collections(
    pageNum: int = Query(1, ge=1, description="페이지 번호"),
    pageSize: int = Query(20, ge=1, le=100, description="페이지 크기"),
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

    items, total_items = await list_collections_service(
        session,
        user_no=x_user_uuid,
        limit=limit,
        offset=offset,
    )

    total_pages = math.ceil(total_items / pageSize) if total_items > 0 else 0
    has_next = pageNum < total_pages

    return BaseResponse[Dict[str, Any]](
        status=200,
        code="OK",
        message="Fetched collections successfully.",
        isSuccess=True,
        result={
            "data": {
                "data": items,
                "pagination": Pagination(
                    pageNum=pageNum,
                    pageSize=pageSize,
                    totalItems=total_items,
                    totalPages=total_pages,
                    hasNext=has_next,
                ),
            }
        },
    )
