from abc import ABC, abstractmethod
from typing import Dict, Any
from loguru import logger


class BaseExtractionStrategy(ABC):
    """파일 추출 전략 Base 클래스"""
    
    def __init__(self, parameters: Dict[Any, Any] = None):
        self.parameters = parameters or {}
        logger.info(f"Initialized {self.__class__.__name__} with parameters: {self.parameters}")
    
    @abstractmethod
    def extract(self, file_path: str) -> Dict[Any, Any]:
        """파일 추출 처리"""
        pass

