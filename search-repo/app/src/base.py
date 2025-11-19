from abc import ABC, abstractmethod
from typing import Dict, Any, List
from loguru import logger


class BaseSearchStrategy(ABC):
    """검색 전략 Base 클래스"""
    
    def __init__(self, parameters: Dict[Any, Any] = None):
        self.parameters = parameters or {}
        logger.info(f"Initialized {self.__class__.__name__} with parameters: {self.parameters}")
    
    @abstractmethod
    def search(self, query_embedding: Dict[Any, Any], collection: str = None, top_k: int = 5) -> Dict[Any, Any]:
        """
        쿼리 임베딩을 사용하여 벡터 저장소에서 검색
        
        Args:
            query_embedding: 쿼리 임베딩 딕셔너리
            collection: 컬렉션 이름
            top_k: 반환할 상위 k개 결과
        
        Returns:
            검색 결과 딕셔너리
        """
        pass

