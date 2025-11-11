from __future__ import annotations
import asyncio

from fastapi import APIRouter, Depends, File as FFile, UploadFile, Request, HTTPException, status, Query, BackgroundTasks
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from datetime import datetime, timezone

from app.core.database import get_db
from app.core.schemas import BaseResponse
from ..schemas.response.upload_files import FileUploadBatchResult
from ..services.call_ingest import call_ingest
from ..schemas.request.upload_files import FileUploadRequest
from ..services.upload import upload_files as upload_files_service
from app.core.clients.redis_client import get_redis_client
from app.core.config.settings import settings


router = APIRouter(prefix="/files", tags=["File"])

logger = logging.getLogger(__name__)

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

    files_payload: list[tuple[bytes, str, str | None]] = []
    file_sizes: list[int] = []
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

    # ingest 옵션이 true일 때만 수행
    if autoIngest:
        try:
            redis = get_redis_client()
            n = len(batch_meta.files)
            base = await redis.incrby("ingest:run:seq", n)
            run_ids = [str(base - (n - 1) + i) for i in range(n)]

            pipe = redis.pipeline(transaction=False)
            now_iso = datetime.now(timezone.utc).isoformat()
            for idx, fmeta in enumerate(batch_meta.files):
                run_id = run_ids[idx]
                meta_key = f"ingest:run:{run_id}:meta"
                pipe.hset(
                    meta_key,
                    mapping={
                        "userId": x_user_uuid,
                        "fileNo": fmeta.fileNo,
                        "fileName": fmeta.fileName,
                        "fileCategory": request.category,
                        "bucket": batch_meta.bucket,
                        "size": str(file_sizes[idx]),
                        "status": "PENDING",
                        "currentStep": "UPLOAD",
                        "progressPct": "0",
                        "overallPct": "0",
                        "createdAt": now_iso,
                        "updatedAt": now_iso,
                    },
                )
                if getattr(settings, "ingest_meta_ttl_sec", 0) > 0:
                    pipe.expire(meta_key, settings.ingest_meta_ttl_sec)
                pipe.sadd(f"ingest:user:{x_user_uuid}:runs", run_id)
            await pipe.execute()
        except Exception:
            logger.exception("Failed to write ingest run metadata to Redis")

        # ingest 비동기 호출
        if background_tasks is not None:
            try:
                background_tasks.add_task(
                    call_ingest,
                    user_role=role_upper,
                    user_uuid=x_user_uuid,
                    batch_meta=batch_meta,
                )
            except Exception:
                logger.exception("Failed to register background ingest task")

    return BaseResponse[FileUploadBatchResult](
        status=201,
        code="CREATED",
        message="업로드 완료",
        isSuccess=True,
        result={"data": FileUploadBatchResult(fileNos=file_nos)},
    )