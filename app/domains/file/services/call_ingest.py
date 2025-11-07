from __future__ import annotations

import logging
from typing import Any

import httpx

from app.core.settings import settings
from app.domains.file.schemas.response.upload_files import UploadBatchMeta


logger = logging.getLogger(__name__)


async def call_ingest(*, user_role: str, batch_meta: UploadBatchMeta) -> None:
    """Call external ingest API with the uploaded files metadata.

    Non-blocking usage is recommended via FastAPI BackgroundTasks.
    """
    payload: dict[str, Any] = {
        "userRole": user_role,
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

    url = getattr(settings, "ingest_process_url", None) or "https://gateway.ragextension.shop/rag/ingest/process"
    timeout = httpx.Timeout(20.0, connect=5.0)
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            logger.info("Ingest call success: status=%s", resp.status_code)
    except Exception as e:
        logger.exception("Ingest call failed: %s", e)