from pydantic import BaseModel
from typing import Optional, Dict, Any


class QueryEmbeddingProcessRequest(BaseModel):
    """Query Embedding /process 요청 스키마"""
    query: str
    queryEmbeddingStrategy: str
    queryEmbeddingParameter: Dict[Any, Any] = {}

