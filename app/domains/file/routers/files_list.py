from __future__ import annotations

from fastapi import APIRouter, Depends, Header, Request, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.schemas import BaseResponse
from ..schemas.response.files import FileListItem
from ..services import files as files_service


router = APIRouter(prefix="/files", tags=["File"])


@router.get("", response_model=BaseResponse[list[FileListItem]])
async def list_my_files(
    limit: int = 20,
    offset: int = 0,
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

    items = await files_service.list_files_by_offer(
        session,
        user_no=x_user_uuid,
        limit=limit,
        offset=offset,
        category_no=category,
    )

    return BaseResponse[list[FileListItem]](
        status=200,
        code="OK",
        message="문서 목록 조회에 성공했습니다.",
        isSuccess=True,
        result={"data": items},
    )
