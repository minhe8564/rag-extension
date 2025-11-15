from abc import ABC, abstractmethod
from typing import Dict, Any, List
from loguru import logger


class BaseChunkingStrategy(ABC):
    """청킹 전략 Base 클래스"""
    
    def __init__(self, parameters: Dict[Any, Any] = None):
        self.parameters = parameters or {}
        logger.info(f"Initialized {self.__class__.__name__} with parameters: {self.parameters}")
    
    @abstractmethod
    def chunk(self, pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        페이지 데이터를 청크로 나누기
        
        Args:
            pages: 페이지 리스트, 각 페이지는 {"page": int, "content": str} 형식
        
        Returns:
            청크 리스트, 각 청크는 {"doc_id": str, "page": int, "chunk_id": int, "text": str} 형식
        """
        pass

