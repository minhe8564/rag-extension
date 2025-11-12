from __future__ import annotations

from fastapi import APIRouter, Request, HTTPException, status, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.schemas import BaseResponse
from app.core.database import get_db
from ..schemas.response.presigned_url import PresignedUrl
from ..services.presign import generate_presigned_url_with_auth


router = APIRouter(prefix="/files", tags=["File"])


@router.get("/{fileNo}/presigned", response_model=BaseResponse[PresignedUrl])
async def generate_presigned_url_by_file_no(
    fileNo: str,
    http_request: Request,
    session: AsyncSession = Depends(get_db),
    days: int = Query(7, ge=1, le=7, description="만료 일수(1~7일)"),
    inline: bool = Query(False, description="표시 방식(true=inline, false=download). 기본값: download"),
    contentType: str | None = Query(None, description="응답 Content-Type 강제 지정"),
    versionId: str | None = Query(None, description="특정 버전 ID"),
):
    x_user_role = http_request.headers.get("x-user-role")
    x_user_uuid = http_request.headers.get("x-user-uuid")
    if not x_user_role or not x_user_uuid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="x-user-role/x-user-uuid headers required")

    role_upper = (x_user_role or "").upper()

    url = await generate_presigned_url_with_auth(
        session,
        file_no=fileNo,
        role=role_upper,
        user_uuid=x_user_uuid,
        days=days,
        inline=inline,
        content_type=contentType,
        version_id=versionId,
    )

    return BaseResponse[PresignedUrl](
        status=200,
        code="OK",
        message="Presigned URL 생성 완료",
        isSuccess=True,
        result={"data": PresignedUrl(url=url)},
    )
