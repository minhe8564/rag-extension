from abc import ABC, abstractmethod
from typing import Dict, Any, List
from loguru import logger


class BaseGenerationStrategy(ABC):
    """생성 전략 Base 클래스"""
    
    def __init__(self, parameters: Dict[Any, Any] = None):
        self.parameters = parameters or {}
        logger.info(f"Initialized {self.__class__.__name__} with parameters: {self.parameters}")
    
    @abstractmethod
    def generate(
        self,
        query: str,
        retrieved_chunks: List[Dict[str, Any]],
        memory=None
    ) -> Dict[Any, Any]:
        """
        쿼리와 검색된 청크를 사용하여 최종 답변 생성
        
        Args:
            query: 검색 쿼리 문자열
            retrieved_chunks: 검색된 청크 리스트
            memory: LangChain memory 객체 (선택적, history 기능용)
        
        Returns:
            생성된 답변 딕셔너리
        """
        pass

