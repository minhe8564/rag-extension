from __future__ import annotations

from fastapi import APIRouter, Depends, Request, HTTPException, status, File as FFile, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.schemas import BaseResponse
from app.core.check_role import check_role  # kept for other routes; not used here
from ..schemas.response.upload_file import FileUploadResult
from ..schemas.request.upload_file import FileUploadRequest
from ..services.files import upload_file as upload_file_service


router = APIRouter(prefix="/files", tags=["File"])


# Local dependencies that read headers directly (kept out of OpenAPI params)
def _require_user_or_admin(request: Request) -> str:
    role = request.headers.get("x-user-role")
    if role is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="x-user-role header is required")
    if role not in {"USER", "ADMIN"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden role")
    return role


def _get_user_uuid(request: Request) -> str:
    user_uuid = request.headers.get("x-user-uuid")
    if not user_uuid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="x-user-uuid header is required")
    return user_uuid

@router.post("/", response_model=BaseResponse[FileUploadResult], status_code=201)
async def upload_file(
    request: FileUploadRequest = Depends(FileUploadRequest.as_form),
    file: UploadFile = FFile(...),
    x_user_role: str = Depends(_require_user_or_admin),
    x_user_uuid: str = Depends(_get_user_uuid),
    session: AsyncSession = Depends(get_db),
):
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
