from pydantic import BaseModel
from typing import List, Dict, Any


class Chunk(BaseModel):
    """Chunk 스키마"""
    page: int
    chunk_id: int
    text: str


class ChunkingProcessResult(BaseModel):
    """Chunking Process 결과 스키마"""
    chunks: List[Chunk]
    chunk_count: int
    strategy: str
    strategyParameter: Dict[str, Any]


class ChunkingProcessResponse(BaseModel):
    """Chunking /process 응답 스키마"""
    status: int
    code: str
    message: str
    isSuccess: bool
    result: ChunkingProcessResult




