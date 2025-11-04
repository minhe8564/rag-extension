from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, File as FFile, UploadFile, Form, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ....common.db import get_session
from ....common.schemas import BaseResponse
from ..schemas.files import FileUploadResult
from ..services.files import upload_file as upload_file_service


router = APIRouter(prefix="/files", tags=["File"])


@router.post("/", response_model=BaseResponse[FileUploadResult], status_code=201)
async def upload_file(
    userNo: str = Query(..., description="업로더 USER_NO (UUID)"),
    onNameConflict: str = Query("reject", description="파일명 충돌 정책: reject|rename|overwrite"),
    file: UploadFile = FFile(...),
    category: str = Form(..., description="FILE_CATEGORY_NO (UUID)"),
    bucket: Optional[str] = Form(None, description="public|private|test (관리자 전용)"),
    collection: Optional[str] = Form(None, description="COLLECTION_NO (UUID, 관리자 전용)"),
    autoIngest: Optional[bool] = Form(False, description="ingest 수행 여부 (현재 미사용)"),
    session: AsyncSession = Depends(get_session),
):
    file_bytes = await file.read()
    file_no = await upload_file_service(
        session,
        file_bytes=file_bytes,
        original_filename=file.filename or "uploaded",
        content_type=file.content_type,
        user_no=userNo,
        category_no=category,
        on_name_conflict=onNameConflict,
        bucket=bucket,
        collection_no=collection,
    )

    return BaseResponse[FileUploadResult](
        status=201,
        code="CREATED",
        message="업로드 성공",
        isSuccess=True,
        result={"data": FileUploadResult(fileNo=file_no)},
    )
