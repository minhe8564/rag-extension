from __future__ import annotations

from fastapi import APIRouter, Depends, File as FFile, UploadFile, Request, HTTPException, status, BackgroundTasks
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
    file_sizes: list[int] = []
    for f in files:
        content = await f.read()
        files_payload.append((content, f.filename or "uploaded", f.content_type))
        file_sizes.append(len(content))

    # Persist and upload files; errors here should fail the request
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
    except HTTPException:
        logger.exception("Upload failed with HTTPException")
        raise
    except Exception:
        logger.exception("Unexpected error during file upload")
        raise

    # Best-effort: write Redis run meta for each file
    try:
        redis = get_redis_client()
        n = len(batch_meta.files)
        run_ids: list[str] = []
        if n > 0:
            base = await redis.incrby("ingest:run:seq", n)
            start = base - (n - 1)
            run_ids = [str(start + i) for i in range(n)]

        pipe = redis.pipeline(transaction=False)

        now_iso = datetime.now(timezone.utc).isoformat()
        # batch_meta.files order matches input order; align sizes accordingly
        for idx, fmeta in enumerate(batch_meta.files):
            run_id = run_ids[idx] if idx < len(run_ids) else str(idx)
            meta_key = f"ingest:run:{run_id}:meta"
            # HSET with required fields
            pipe.hset(
                meta_key,
                mapping={
                    "userId": x_user_uuid,
                    "fileNo": fmeta.fileNo,
                    "fileName": fmeta.fileName,
                    "fileCategory": request.category,
                    "bucket": batch_meta.bucket,
                    "size": str(file_sizes[idx]) if idx < len(file_sizes) else "0",
                    "status": "PENDING",
                    "currentStep": "UPLOAD",
                    "progressPct": "0",
                    "overallPct": "0",
                    "createdAt": now_iso,
                    "updatedAt": now_iso,
                },
            )
            # optional TTL
            if getattr(settings, "ingest_meta_ttl_sec", 0) and settings.ingest_meta_ttl_sec > 0:
                pipe.expire(meta_key, settings.ingest_meta_ttl_sec)
            # Add run id to user's running set
            pipe.sadd(f"ingest:user:{x_user_uuid}:runs", run_id)

        await pipe.execute()
    except Exception:
        logger.exception("Failed to write ingest run metadata to Redis")

    # Then register background ingest task (best-effort)
    if background_tasks is not None:
        try:
            background_tasks.add_task(
                call_ingest,
                user_role=x_user_role,
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
        result={
            "data": FileUploadBatchResult(
                fileNos=file_nos,
            )
        },
    )
