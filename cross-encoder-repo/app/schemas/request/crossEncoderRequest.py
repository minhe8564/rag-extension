from pydantic import BaseModel
from typing import Dict, Any, List


class CrossEncoderProcessRequest(BaseModel):
    """Cross Encoder /process 요청 스키마"""
    query: str
    candidateEmbeddings: List[Dict[str, Any]]
    crossEncoderStrategy: str
    crossEncoderParameter: Dict[Any, Any] = {}

