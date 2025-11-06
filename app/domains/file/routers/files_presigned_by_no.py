from __future__ import annotations

from fastapi import APIRouter, Request, HTTPException, status, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.core.schemas import BaseResponse
from app.core.database import get_db
from ..schemas.response.presigned_url import PresignedUrl
from ..services import files as files_service
from ..repositories.file_repository import FileRepository


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

    try:
        file_no_bytes = uuid.UUID(fileNo).bytes
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid fileNo format (UUID required)")

    file_rec = await FileRepository.find_by_file_no(session, file_no_bytes)
    if not file_rec:
        raise HTTPException(status_code=404, detail="File not found")

    if x_user_role != "ADMIN":
        try:
            user_no_bytes = uuid.UUID(x_user_uuid).bytes
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid x-user-uuid format (UUID required)")
        offer_no = await files_service._get_offer_no_by_user(session, user_no_bytes)
        if file_rec.offer_no != offer_no:
            raise HTTPException(status_code=403, detail="Forbidden: file does not belong to your offer")

    url = await files_service.get_presigned_url(
        bucket=file_rec.bucket,
        object_name=file_rec.path,
        content_type=contentType,
        days=days,
        version_id=versionId,
        inline=inline,
    )

    return BaseResponse[PresignedUrl](
        status=200,
        code="OK",
        message="Presigned URL 생성 완료",
        isSuccess=True,
        result={"data": PresignedUrl(url=url)},
    )
