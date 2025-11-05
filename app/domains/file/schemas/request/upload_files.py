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

    onNameConflict: Literal["reject", "overwrite"] = "reject"
    category: str
    bucket: Optional[str] = None

    @classmethod
    def as_form(
        cls,
        onNameConflict: Literal["reject", "overwrite"] = Query(
            "reject", description="파일명 충돌 정책: reject|overwrite"
        ),
        category: str = Form(..., description="FILE_CATEGORY_NO (UUID)"),
        bucket: Optional[str] = Form(None, description="public|private|test (선택)"),
    ) -> "FileUploadRequest":
        return cls(
            onNameConflict=onNameConflict,
            category=category,
            bucket=bucket,
        )