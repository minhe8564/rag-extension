from pydantic import BaseModel
from typing import Optional, Dict, Any, List


class GenerationProcessRequest(BaseModel):
    """Generation /process 요청 스키마"""
    query: str
    retrievedChunks: List[Dict[str, Any]]
    generationStrategy: str
    generationParameter: Dict[Any, Any] = {}
    # History 관련 필드 (항상 memory 사용, userId와 sessionId가 있으면 활성화)
    userId: Optional[str] = None
    sessionId: Optional[str] = None

