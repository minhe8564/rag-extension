from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.schemas import BaseResponse
from ..schemas.response.collection import CollectionListItem
from ..services.collections import list_collections_by_offer as list_collections_service


router = APIRouter(prefix="/collections", tags=["Collection"])


@router.get("", response_model=BaseResponse[List[CollectionListItem]])
async def list_collections(
    limit: int = 20,
    offset: int = 0,
    session: AsyncSession = Depends(get_db),
    http_request: Request = None,
):
    if http_request is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Request context unavailable")

    x_user_role = http_request.headers.get("x-user-role")
    x_user_uuid = http_request.headers.get("x-user-uuid")
    if not x_user_role or not x_user_uuid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="x-user-role/x-user-uuid headers required")

    items: List[CollectionListItem] = await list_collections_service(
        session,
        user_no=x_user_uuid,
        limit=limit,
        offset=offset,
    )

    return BaseResponse[List[CollectionListItem]](
        status=200,
        code="OK",
        message="컬렉션 목록 조회에 성공했습니다.",
        isSuccess=True,
        result={"data": items},
    )
