from pydantic import BaseModel
from typing import List, Dict, Any


class RetrievedChunk(BaseModel):
    """Retrieved Chunk 스키마"""
    page: int
    chunk_id: int
    text: str
    score: float
    fileNo: str
    fileName: str


class CrossEncoderProcessResult(BaseModel):
    """Cross Encoder Process 결과 스키마"""
    query: str
    retrievedChunks: List[RetrievedChunk]
    count: int
    strategy: str
    parameters: Dict[Any, Any]


class CrossEncoderProcessResponse(BaseModel):
    """Cross Encoder /process 응답 스키마"""
    status: int
    code: str
    message: str
    isSuccess: bool
    result: CrossEncoderProcessResult









