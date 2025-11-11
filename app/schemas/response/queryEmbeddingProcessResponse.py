from pydantic import BaseModel
from typing import List, Dict, Any


class QueryEmbeddingProcessResult(BaseModel):
    """Query Embedding Process 결과 스키마"""
    query: str
    embedding: List[float]
    dimension: int
    strategy: str
    parameters: Dict[Any, Any]


class QueryEmbeddingProcessResponse(BaseModel):
    """Query Embedding /process 응답 스키마"""
    status: int
    code: str
    message: str
    isSuccess: bool
    result: QueryEmbeddingProcessResult









