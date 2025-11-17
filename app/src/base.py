from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from loguru import logger


class BaseChunkingStrategy(ABC):
    """청킹 전략 Base 클래스"""
    
    def __init__(self, parameters: Dict[Any, Any] = None):
        self.parameters = parameters or {}
        logger.info(f"Initialized {self.__class__.__name__} with parameters: {self.parameters}")
    
    @abstractmethod
    def chunk(self, bucket: str, path: str, request_headers: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        원격 저장소 객체(bucket/path)를 presigned URL로 다운로드하여 청킹
        
        Args:
            bucket: 버킷 이름 (예: "ingest")
            path:   객체 키 (예: "user/abc.md")
            request_headers: 호출자 헤더(예: x-user-uuid, x-user-role)
        
        Returns:
            청크 리스트, 각 청크는 {"page": int, "chunk_id": int, "text": str} 형식
        """
        raise NotImplementedError()

