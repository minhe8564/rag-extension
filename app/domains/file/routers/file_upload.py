from __future__ import annotations

import logging
from importlib import import_module
from datetime import datetime, timezone

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
from app.core.clients.redis_client import get_metrics_redis_client, get_redis_client
from app.core.config.settings import settings
from importlib import import_module

try:
    _redis_exceptions = import_module("redis.exceptions")
    REDIS_ERROR_TYPES = (_redis_exceptions.RedisError,)
except ModuleNotFoundError:
    class _RedisErrorFallback(Exception):
        """Fallback used when redis.exceptions is unavailable."""

UPLOAD_COUNT_KEY = "metrics:uploads:total_count"


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

    uploaded_files_count = len(batch_meta.files)
    metrics_redis = None
    try:
        metrics_redis = get_metrics_redis_client()
    except RuntimeError:
        logger.exception("Failed to acquire Redis client for upload metrics")

    if metrics_redis is not None and uploaded_files_count:
        try:
            await metrics_redis.incrby(UPLOAD_COUNT_KEY, uploaded_files_count)
        except REDIS_ERROR_TYPES:
            logger.exception("Failed to increment upload metrics in Redis")

    # ingest 옵션이 true일 때만 수행
    if autoIngest:
        try:
            redis = get_redis_client()
            n = len(batch_meta.files)
            base = await redis.incrby("ingest:run:seq", n)
            run_ids = [str(base - (n - 1) + i) for i in range(n)]

            pipe = redis.pipeline(transaction=False)
            now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
            now_iso = datetime.now(timezone.utc).isoformat()
            for idx, fmeta in enumerate(batch_meta.files):
                run_id = run_ids[idx]
                meta_key = f"ingest:run:{run_id}:meta"
                events_key = f"ingest:run:{run_id}:events"
                pipe.hset(
                    meta_key,
                    mapping={
                        "userId": x_user_uuid,
                        "fileNo": fmeta.fileNo,
                        "fileName": fmeta.fileName,
                        "fileCategory": request.category,
                        "bucket": batch_meta.bucket,
                        "size": str(file_sizes[idx]),
                        "status": "RUNNING",
                        "currentStep": "UPLOAD",
                        "progressPct": "100",
                        "overallPct": "20",
                        "createdAt": now_iso,
                        "updatedAt": now_iso,
                    },
                )
                if getattr(settings, "ingest_meta_ttl_sec", 0) > 0:
                    pipe.expire(meta_key, settings.ingest_meta_ttl_sec)
                pipe.sadd(f"ingest:user:{x_user_uuid}:runs", run_id)

                # 파일번호로 최신 runId 조회용 STRING 키 저장
                file_latest_key = f"ingest:file:{fmeta.fileNo}:latest_run_id"
                pipe.set(file_latest_key, run_id)
                if getattr(settings, "ingest_meta_ttl_sec", 0) > 0:
                    pipe.expire(file_latest_key, settings.ingest_meta_ttl_sec)
                    
                pipe.xadd(
                    events_key,
                    fields={
                        "type": "STEP_UPDATE",
                        "runId": run_id,               # Long/숫자 문자열 OK
                        "docId": "",                   # 없으면 빈값 (또는 fileNo 사용 시 클라이언트 매핑)
                        "docName": fmeta.fileName,
                        "step": "UPLOAD",              # DTO의 step 필드명에 맞춤
                        "processed": "1",              # 있으면 설정, 없으면 "0"
                        "total": "1",
                        "progressPct": "100",
                        "overallPct": "20",
                        "status": "RUNNING",
                        "ts": str(now_ms),
                    },
                    id="*",                          # 서버에서 ms-time 기반 ID 부여
                    maxlen=1000,                     # 스트림 길이 관리 (approximate trim)
                    approximate=True,
                )

            # 유저 단위 summary 진행률 업데이트 (hash + stream)
            try:
                summary_key = f"ingest:summary:user:{x_user_uuid}"
                summary = await redis.hgetall(summary_key)
                prev_total = 0
                prev_completed = 0
                if summary:
                    try:
                        prev_total = int(summary.get("total", 0) or 0)
                    except (TypeError, ValueError):
                        prev_total = 0
                    try:
                        prev_completed = int(summary.get("completed", 0) or 0)
                    except (TypeError, ValueError):
                        prev_completed = 0

                # 진행 중 라운드가 있다면 total에 누적, 아니면 새 라운드 시작
                if prev_total > 0 and prev_completed < prev_total:
                    total = prev_total + n
                    completed = prev_completed
                else:
                    total = n
                    completed = 0

                await redis.hset(
                    summary_key,
                    mapping={
                        "total": str(total),
                        "completed": str(completed),
                        "updatedAt": now_iso,
                    },
                )

                # summary용 스트림 이벤트 추가 (event: summary)
                await redis.xadd(
                    "ingest:summary",
                    fields={
                        "eventType": "SUMMARY",
                        "userId": x_user_uuid,
                        "completed": str(completed),
                        "total": str(total),
                        "ts": str(now_ms),
                    },
                    maxlen=1000,
                    approximate=True,
                )
            except REDIS_ERROR_TYPES:
                logger.exception("Failed to update ingest summary in Redis")

            await pipe.execute()
        except RuntimeError:
            logger.exception("Failed to acquire Redis client for ingest metadata")
        except REDIS_ERROR_TYPES:
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
            except RuntimeError:
                logger.exception("Failed to register background ingest task")

    return BaseResponse[FileUploadBatchResult](
        status=201,
        code="CREATED",
        message="업로드 완료",
        isSuccess=True,
        result={"data": FileUploadBatchResult(fileNos=file_nos)},
    )
