from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


class IngestProgressEvent(BaseModel):
    # Required linkage
    runId: Optional[str] = Field(None, description="Ingest run identifier")

    # Optional context
    userId: Optional[str] = Field(None, description="User UUID")
    fileNo: Optional[str] = Field(None, description="File UUID")

    # Step/status/progress
    currentStep: Optional[str] = Field(
        None, description="UPLOAD|EXTRACTION|CHUNKING|EMBEDDING|VECTOR_STORE"
    )
    status: Optional[str] = Field(
        None, description="PENDING|RUNNING|COMPLETED|FAILED"
    )
    processed: Optional[int] = Field(None, description="Processed count for this step")
    total: Optional[int] = Field(None, description="Total count for this step")

    # Optional explicit event type/ts
    eventType: Optional[str] = Field(
        None,
        description="STEP_START|STEP_UPDATE|STEP_END|RUN_COMPLETED|RUN_FAILED, inferred if absent",
    )
    ts: Optional[int] = Field(None, description="Event timestamp in epoch ms")

