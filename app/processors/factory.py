"""
프로세서 팩토리
파일 형식에 맞는 프로세서를 반환
"""

from pathlib import Path
from typing import List

from .base import BaseProcessor
from .pdf_processor import PDFProcessor
from .txt_processor import TXTProcessor
from .excel_processor import ExcelProcessor

class ProcessorFactory:
    """
    파일 형식에 맞는 프로세서를 반환하는 팩토리
    """

    _processors: List[BaseProcessor] = [
        PDFProcessor(),
        TXTProcessor(),
        ExcelProcessor(),
    ]

    @classmethod
    def get_processor(cls, file_path: str) -> BaseProcessor:
        """
        파일 경로에 맞는 프로세서 반환
        """
        for processor in cls._processors:
            if processor.can_process(file_path):
                return processor
        
        ext = Path(file_path).suffix.lower()
        raise ValueError(f"지원하지 않는 파일 형식입니다: {ext}")
    
    @classmethod
    def get_supported_extensions(cls) -> List[str]:
        """
        모든 지원 확장자 반환
        """
        extensions = []
        for processor in cls._processors:
            extensions.extend(processor.supported_extensions)

        return list(set(extensions))