from pydantic import BaseModel
from typing import Optional, Dict, Any, List


class ChunkingProcessRequest(BaseModel):
    """Chunking /process 요청 스키마"""
    pages: List[Dict[str, Any]]  # [{"page": 1, "content": "~"}, ...]
    chunkingStrategy: str
    chunkingParameter: Dict[Any, Any] = {}

