from __future__ import annotations

from fastapi import APIRouter, Request, HTTPException, status, Query

from app.core.schemas import BaseResponse
from ..schemas.response.presigned_url import PresignedUrl
from ..services.presign import get_presigned_url


router = APIRouter(prefix="/files", tags=["File"])


@router.get("/presigned", response_model=BaseResponse[PresignedUrl])
async def generate_presigned_url(
    http_request: Request,
    bucket: str = Query(..., description="대상 버킷 이름"),
    path: str = Query(..., description="객체 키(경로 포함)"),
    contentType: str | None = Query(None, description="응답 Content-Type 지정"),
    days: int = Query(7, ge=1, le=7, description="만료 일수(1~7일)"),
    versionId: str | None = Query(None, description="특정 버전 ID"),
    inline: bool = Query(True, description="브라우저 표시 여부(true=inline, false=download)"),
):
    x_user_role = http_request.headers.get("x-user-role")
    x_user_uuid = http_request.headers.get("x-user-uuid")
    if not x_user_role or not x_user_uuid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="x-user-role/x-user-uuid headers required")

    url = await get_presigned_url(
        bucket=bucket,
        object_name=path,
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

