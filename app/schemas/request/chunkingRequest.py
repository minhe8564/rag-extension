from pydantic import BaseModel
from typing import Optional, Dict, Any


class ChunkingProcessRequest(BaseModel):
    """Chunking /process 요청 스키마
    - presigned 다운로드를 위한 bucket/path만 입력으로 받습니다.
    """
    bucket: str
    path: str
    chunkingStrategy: str
    chunkingParameter: Dict[Any, Any] = {}

