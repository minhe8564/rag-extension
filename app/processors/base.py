"""
프로세서 추상 베이스 클래스
모든 파일 프로세서가 구현해야 하는 인터페이스
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, List

class BaseProcessor(ABC):
    """
    파일 프로세서 추상 베이스 클래스
    """

    @property
    @abstractmethod
    def supported_extensions(self) -> List[str]:
        """
        지원하는 파일 확장자 리스트
        """
        pass

    @abstractmethod
    def process(self, file_path: str) -> Dict[str, Any]:
        """
        파일을 처리하여 결과 반환
        """
        pass

    def can_process(self, file_path: str) -> bool:
        """
        파일이 처리 가능한지 확인
        """
        ext = Path(file_path).suffix.lower()
        return ext in self.supported_extensions