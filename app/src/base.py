from abc import ABC, abstractmethod
from typing import Dict, Any, List
from loguru import logger


class BaseEmbeddingStrategy(ABC):
    """임베딩 전략 Base 클래스"""
    
    def __init__(self, parameters: Dict[Any, Any] = None):
        self.parameters = parameters or {}
        logger.info(f"Initialized {self.__class__.__name__} with parameters: {self.parameters}")
    
    @abstractmethod
    def embed(self, chunks: List[Dict[str, Any]]) -> Dict[Any, Any]:
        """
        청크 데이터를 임베딩으로 변환
        
        Args:
            chunks: 청크 리스트, 각 청크는 {"page": int, "chunk_id": int, "text": str} 형식
        
        Returns:
            임베딩 결과 딕셔너리
        """
        pass

