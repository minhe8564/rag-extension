from abc import ABC, abstractmethod
from typing import Dict, Any, List
from loguru import logger


class BaseCrossEncoderStrategy(ABC):
    """Cross Encoder 전략 Base 클래스"""
    
    def __init__(self, parameters: Dict[Any, Any] = None):
        self.parameters = parameters or {}
        logger.info(f"Initialized {self.__class__.__name__} with parameters: {self.parameters}")
    
    @abstractmethod
    def rerank(self, query_embedding: Dict[Any, Any], candidate_embeddings: List[Dict[str, Any]]) -> Dict[Any, Any]:
        """
        쿼리 임베딩과 후보 임베딩들을 cross-encoder로 재정렬
        
        Args:
            query_embedding: 쿼리 임베딩 딕셔너리
            candidate_embeddings: 후보 임베딩 리스트
        
        Returns:
            재정렬된 결과 딕셔너리
        """
        pass

