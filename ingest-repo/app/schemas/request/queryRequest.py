from typing import Dict, Any
from pydantic import BaseModel


class QueryProcessRequest(BaseModel):
    """Query /process 요청 스키마"""
    query: str
    collectionName: str
    queryEmbeddingStrategy: str
    queryEmbeddingParameter: Dict[Any, Any] = {}
    searchStrategy: str
    searchParameter: Dict[Any, Any] = {}
    crossEncoderStrategy: str
    crossEncoderParameter: Dict[Any, Any] = {}
    generationStrategy: str
    generationParameter: Dict[Any, Any] = {}

