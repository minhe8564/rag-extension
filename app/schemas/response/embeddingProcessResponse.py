from pydantic import BaseModel
from typing import List, Dict, Any, Optional


class EmbeddedChunk(BaseModel):
    """Embedded Chunk 스키마"""
    page: int
    chunk_id: int
    text: str
    embedding: List[float]


class EmbeddingProcessResult(BaseModel):
    """Embedding Process 결과 스키마"""
    count: int
    embedding_dimension: int
    collectionName: Optional[str] = None
    strategy: str
    strategyParameter: Dict[str, Any]


class EmbeddingProcessResponse(BaseModel):
    """Embedding /process 응답 스키마"""
    status: int
    code: str
    message: str
    isSuccess: bool
    result: EmbeddingProcessResult




