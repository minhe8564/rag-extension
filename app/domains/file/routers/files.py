from __future__ import annotations

from fastapi import APIRouter, Depends, File as FFile, UploadFile, Header, Request, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.schemas import BaseResponse
from ..schemas.response.upload_file import FileUploadResult
from ..schemas.request.upload_file import FileUploadRequest
from ..services.files import upload_file as upload_file_service


router = APIRouter(prefix="/files", tags=["File"])

@router.post("/", response_model=BaseResponse[FileUploadResult], status_code=201)
async def upload_file(
    request: FileUploadRequest = Depends(FileUploadRequest.as_form),
    file: UploadFile = FFile(...),
    session: AsyncSession = Depends(get_db),
    http_request: Request = None,
):
    if http_request is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Request context unavailable")
    x_user_role = http_request.headers.get("x-user-role")
    x_user_uuid = http_request.headers.get("x-user-uuid")
    if not x_user_role or not x_user_uuid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="x-user-role/x-user-uuid headers required")
    # Role-based branching
    # - USER: ignore provided bucket/collection; use personal (offer_no) bucket
    # - ADMIN: allow explicit bucket/collection
    if x_user_role == "ADMIN":
        effective_bucket = request.bucket
        effective_collection = request.collection
    else:
        effective_bucket = None
        effective_collection = None

    file_bytes = await file.read()
    file_no = await upload_file_service(
        session,
        file_bytes=file_bytes,
        original_filename=file.filename or "uploaded",
        content_type=file.content_type,
        user_no=x_user_uuid,
        category_no=request.category,
        on_name_conflict=request.onNameConflict,
        bucket=effective_bucket,
        collection_no=effective_collection,
    )

    return BaseResponse[FileUploadResult](
        status=201,
        code="CREATED",
        message="업로드 완료",
        isSuccess=True,
        result={"data": FileUploadResult(fileNo=file_no)},
    )
