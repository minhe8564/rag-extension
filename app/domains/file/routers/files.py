from __future__ import annotations

from fastapi import APIRouter, Depends, File as FFile, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from ....common.db import get_session
from ....common.schemas import BaseResponse
from ..schemas.response.upload_file import FileUploadResult
from ..schemas.request.upload_file import FileUploadRequest
from ..services.files import upload_file as upload_file_service


router = APIRouter(prefix="/files", tags=["File"])


@router.post("/", response_model=BaseResponse[FileUploadResult], status_code=201)
async def upload_file(
    req: FileUploadRequest = Depends(FileUploadRequest.as_form),
    file: UploadFile = FFile(...),
    session: AsyncSession = Depends(get_session),
):
    file_bytes = await file.read()
    file_no = await upload_file_service(
        session,
        file_bytes=file_bytes,
        original_filename=file.filename or "uploaded",
        content_type=file.content_type,
        user_no=req.userNo,
        category_no=req.category,
        on_name_conflict=req.onNameConflict,
        bucket=req.bucket,
        collection_no=req.collection,
    )

    return BaseResponse[FileUploadResult](
        status=201,
        code="CREATED",
        message="업로드 완료",
        isSuccess=True,
        result={"data": FileUploadResult(fileNo=file_no)},
    )
