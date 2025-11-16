from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from fastapi import APIRouter, Depends, File as FFile, UploadFile, Request, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.schemas import BaseResponse
from ..schemas.response.upload_files import FileUploadBatchResult
from ..services.call_ingest import call_ingest
from ..schemas.request.upload_files import FileUploadRequest
from ..services.upload import upload_files as upload_files_service
from app.core.clients.redis_client import get_metrics_redis_client

router = APIRouter(prefix="/files", tags=["File"])

logger = logging.getLogger(__name__)

UPLOAD_STREAM_KEY = "upload:files"


@router.post("", response_model=BaseResponse[FileUploadBatchResult], status_code=201)
async def upload_file(
    http_request: Request,
    background_tasks: BackgroundTasks,
    request: FileUploadRequest = Depends(FileUploadRequest.as_form),
    files: List[UploadFile] = FFile(...),
    session: AsyncSession = Depends(get_db),
    autoIngest: bool = Query(
        True,
        description="업로드 후 백그라운드 Ingest 실행 여부 (true=실행, false=미실행)",
    ),
):
    x_user_role = http_request.headers.get("x-user-role")
    x_user_uuid = http_request.headers.get("x-user-uuid")
    if not x_user_role or not x_user_uuid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="x-user-role/x-user-uuid headers required",
        )

    role_upper = (x_user_role or "").upper()
    if role_upper == "ADMIN":
        effective_bucket = request.bucket
        effective_collection = None
    else:
        effective_bucket = None
        effective_collection = None

    files_payload: List[Tuple[bytes, str, Optional[str]]] = []
    file_sizes: List[int] = []
    for f in files:
        content = await f.read()
        files_payload.append((content, f.filename or "uploaded", f.content_type))
        file_sizes.append(len(content))

    try:
        batch_meta, file_nos = await upload_files_service(
            session,
            files=files_payload,
            user_no=x_user_uuid,
            category_no=request.category,
            on_name_conflict=request.onNameConflict,
            bucket=effective_bucket,
            collection_no=effective_collection,
            user_role=role_upper,
        )
    except Exception:
        logger.exception("Upload failed")
        raise

    metrics_redis = None
    try:
        metrics_redis = get_metrics_redis_client()
    except RuntimeError:
        logger.exception("Failed to acquire Redis client for upload stream")

    if metrics_redis is not None:
        now_iso = datetime.now(timezone.utc).isoformat()
        now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
        try:
            for idx, uploaded in enumerate(batch_meta.files):
                await metrics_redis.xadd(
                    UPLOAD_STREAM_KEY,
                    fields={
                        "eventType": "UPLOAD",
                        "userId": x_user_uuid,
                        "role": role_upper,
                        "fileNo": str(uploaded.fileNo),
                        "fileName": uploaded.fileName,
                        "fileCategory": str(request.category or ""),
                        "bucket": batch_meta.bucket or "",
                        "size": str(file_sizes[idx]),
                        "autoIngest": "true" if autoIngest else "false",
                        "uploadedAt": now_iso,
                        "ts": str(now_ms),
                    },
                    maxlen=2000,
                    approximate=True,
                )
        except Exception:
            logger.exception("Failed to publish upload event to Redis stream")

    if autoIngest:
        if background_tasks is not None:
            try:
                background_tasks.add_task(
                    call_ingest,
                    user_role=role_upper,
                    user_uuid=x_user_uuid,
                    batch_meta=batch_meta,
                )
            except RuntimeError:
                logger.exception("Failed to register background ingest task")

    return BaseResponse[FileUploadBatchResult](
        status=201,
        code="CREATED",
        message="업로드 완료",
        isSuccess=True,
        result={"data": FileUploadBatchResult(fileNos=file_nos)},
    )
