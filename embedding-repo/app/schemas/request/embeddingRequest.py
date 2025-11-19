from pydantic import BaseModel
from typing import Optional, Dict, Any, List


class EmbeddingProcessRequest(BaseModel):
    """Embedding /process 요청 스키마"""
    chunks: List[Dict[str, Any]]  # [{"page": 1, "chunk_id": 0, "text": "~"}, ...]
    collectionName: Optional[str] = None
    collectionNo: Optional[str] = None
    bucket: Optional[str] = None
    fileName: Optional[str] = None
    fileNo: Optional[str] = None
    embeddingStrategy: str
    embeddingParameter: Dict[str, Any] = {}

