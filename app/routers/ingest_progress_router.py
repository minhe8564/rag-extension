from __future__ import annotations

from fastapi import APIRouter, HTTPException, Header
from typing import Optional
from loguru import logger

from app.schemas.response.errorResponse import ErrorResponse
from app.schemas.request.ingestProgressEvent import IngestProgressEvent
from app.service.ingest_progress_service import IngestProgressService


router = APIRouter(prefix="/ingest", tags=["ingest-progress"])
progress_service = IngestProgressService()


@router.post("/progress")
async def ingest_progress(
    ev: IngestProgressEvent,
    user_uuid_header: Optional[str] = Header(default=None, alias="x-user-uuid"),
):
    try:
        return await progress_service.push_event(ev, user_uuid_header)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to process ingest progress: {}", e)
        error_response = ErrorResponse(
            status=500,
            code="INTERNAL_ERROR",
            message=f"Internal server error: {str(e)}",
            isSuccess=False,
            result={},
        )
        raise HTTPException(status_code=500, detail=error_response.dict())
