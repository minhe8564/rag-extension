from pydantic import BaseModel
from typing import List, Dict, Any


class SearchProcessRequest(BaseModel):
    """Search /process 요청 스키마"""
    embedding: List[float]
    collectionName: str
    searchStrategy: str
    searchParameter: Dict[Any, Any] = {}

