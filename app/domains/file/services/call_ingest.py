from __future__ import annotations

import logging
import time
from typing import Any

import httpx

from app.core.config.settings import settings
from app.domains.file.schemas.response.upload_files import UploadBatchMeta


logger = logging.getLogger(__name__)


async def call_ingest(user_role: str, user_uuid: str, batch_meta: UploadBatchMeta) -> None:
    """Call external ingest API with the uploaded files metadata.

    Non-blocking usage is recommended via FastAPI BackgroundTasks.
    """
    payload: dict[str, Any] = {
        "bucket": batch_meta.bucket,
        "offerNo": batch_meta.offerNo,
        "files": [
            {
                "fileNo": f.fileNo,
                "fileType": f.fileType,
                "fileName": f.fileName,
                "path": f.path,
            }
            for f in batch_meta.files
        ],
    }

    # 내부 Container 이름으로 호출
    url = settings.ingest_process_url_resolved
    print("Ingest URL:", url)
    timeout = httpx.Timeout(20.0, connect=5.0)
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            headers = {
                "x-user-role": str(user_role),
                "x-user-uuid": str(user_uuid),
            }
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            logger.info("Ingest call success: status=%s", resp.status_code)
    except httpx.ReadTimeout as e:
        # 타임아웃은 클라이언트 기준 오류이므로, 진행률을 FAILED 로 마크하지 않는다.
        logger.exception("Ingest call timed out: %s", e)
    except Exception as e:
        logger.exception("Ingest call failed: %s", e)

        # Ingest 호출이 기타 오류로 실패한 경우에만, 각 파일에 대해 VECTOR_STORE 단계 실패 이벤트를 전송
        try:
            progress_url = f"{settings.ingest_base_url.rstrip('/')}/ingest/progress"
            now_ms = int(time.time() * 1000)
            async with httpx.AsyncClient(timeout=5.0) as client:
                for f in batch_meta.files:
                    body: dict[str, Any] = {
                        "userId": str(user_uuid),
                        "fileNo": f.fileNo,
                        "currentStep": "VECTOR_STORE",
                        "status": "FAILED",
                        "processed": 0,
                        "total": 0,
                        "ts": now_ms,
                    }
                    headers = {"x-user-uuid": str(user_uuid)}
                    try:
                        await client.post(progress_url, json=body, headers=headers)
                    except Exception as pe:
                        # 개별 파일의 실패 이벤트 전송 실패는 전체 흐름을 막지 않는다.
                        logger.debug("Failed to push ingest fail progress for file %s: %s", f.fileNo, pe)
        except Exception as pe:
            logger.debug("Failed to push ingest fail progress events: %s", pe)
