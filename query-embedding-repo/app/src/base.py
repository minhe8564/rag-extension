from abc import ABC, abstractmethod
from typing import Dict, Any
from loguru import logger


class BaseQueryEmbeddingStrategy(ABC):
    """쿼리 임베딩 전략 Base 클래스"""
    
    def __init__(self, parameters: Dict[Any, Any] = None):
        self.parameters = parameters or {}
        logger.info(f"Initialized {self.__class__.__name__} with parameters: {self.parameters}")
    
    @abstractmethod
    def embed(self, query: str) -> Dict[Any, Any]:
        """
        쿼리를 임베딩으로 변환
        
        Args:
            query: 검색 쿼리 문자열
        
        Returns:
            임베딩 결과 딕셔너리
        """
        pass

