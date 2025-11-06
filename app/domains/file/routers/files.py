from __future__ import annotations

from fastapi import APIRouter, Depends, File as FFile, UploadFile, Request, HTTPException, status, BackgroundTasks
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.schemas import BaseResponse
from ..schemas.response.upload_files import FileUploadBatchResult
from ..services.ingest import call_ingest
from ..schemas.request.upload_files import FileUploadRequest
from ..services.files import upload_files as upload_files_service


router = APIRouter(prefix="/files", tags=["File"])


@router.post("", response_model=BaseResponse[FileUploadBatchResult], status_code=201)
async def upload_file(
    http_request: Request,
    request: FileUploadRequest = Depends(FileUploadRequest.as_form),
    files: List[UploadFile] = FFile(...),
    session: AsyncSession = Depends(get_db),
    background_tasks: BackgroundTasks = None,
):
    # Request is injected by FastAPI
    x_user_role = http_request.headers.get("x-user-role")
    x_user_uuid = http_request.headers.get("x-user-uuid")
    if not x_user_role or not x_user_uuid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="x-user-role/x-user-uuid headers required")

    # Role-based branching
    # - USER: ignore provided bucket/collection; use personal (offer_no) bucket
    # - ADMIN: allow explicit bucket/collection
    role_upper = (x_user_role or "").upper()
    if role_upper == "ADMIN":
        effective_bucket = request.bucket
        effective_collection = None
    else:
        effective_bucket = None
        effective_collection = None

    files_payload: list[tuple[bytes, str, str | None]] = []
    for f in files:
        content = await f.read()
        files_payload.append((content, f.filename or "uploaded", f.content_type))

    batch_meta, file_nos = await upload_files_service(
        session,
        files=files_payload,
        user_no=x_user_uuid,
        category_no=request.category,
        on_name_conflict=request.onNameConflict,
        bucket=effective_bucket,
        collection_no=effective_collection,
    )

    if background_tasks is not None:
        background_tasks.add_task(
            call_ingest,
            user_role=role_upper,
            batch_meta=batch_meta,
        )

    return BaseResponse[FileUploadBatchResult](
        status=201,
        code="CREATED",
        message="업로드 완료",
        isSuccess=True,
        result={"data": FileUploadBatchResult(fileNos=file_nos)},
    )
