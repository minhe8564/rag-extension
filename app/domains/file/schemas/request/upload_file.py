from __future__ import annotations

from typing import Literal, Optional

from fastapi import Form, Query
from pydantic import BaseModel


class FileUploadRequest(BaseModel):
    """Schema for file upload request metadata.

    Note: The uploaded file content itself is handled separately via
    FastAPI's `UploadFile` parameter on the route. This schema captures
    associated request fields coming from query/form.
    """

    onNameConflict: Literal["reject", "rename", "overwrite"] = "reject"
    category: str
    bucket: Optional[str] = None
    collection: Optional[str] = None
    autoIngest: Optional[bool] = False

    @classmethod
    def as_form(
        cls,
        onNameConflict: Literal["reject", "rename", "overwrite"] = Query(
            "reject", description="파일명 충돌 정책: reject|rename|overwrite"
        ),
        category: str = Form(..., description="FILE_CATEGORY_NO (UUID)"),
        bucket: Optional[str] = Form(None, description="public|private|test (선택적)"),
        collection: Optional[str] = Form(None, description="COLLECTION_NO (UUID, 선택적)"),
        autoIngest: Optional[bool] = Form(False, description="ingest 자동 여부 (추후 사용)"),
    ) -> "FileUploadRequest":
        return cls(
            onNameConflict=onNameConflict,
            category=category,
            bucket=bucket,
            collection=collection,
            autoIngest=autoIngest,
        )
