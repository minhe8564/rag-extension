from __future__ import annotations

from pydantic import BaseModel
from typing import List


class FileUploadBatchResult(BaseModel):
    fileNos: List[str]

