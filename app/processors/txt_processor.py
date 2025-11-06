"""
TXT 프로세서
TXT 파일을 Markdown으로 변환
"""

import logging
from pathlib import Path
from typing import Dict, Any, List

from .base import BaseProcessor

logger = logging.getLogger(__name__)

class TXTProcessor(BaseProcessor):
    """
    TXT 파일을 Markdown으로 변환하는 프로세서
    """

    @property
    def supported_extensions(self) -> List[str]:
        """
        지원하는 파일 확장자
        """
        
        return [".txt"]
    
    def process(self, file_path: str) -> Dict[str, Any]:
        """
        TXT 파일 -> Markdown 변환
        """
        if not Path(file_path).exists():
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")
            
        try:
            # 여러 인코딩 시도 (UTF-8 우선, 그 다음 CP949, EUC-KR 등)
            encodings = ['utf-8', 'utf-8-sig', 'cp949', 'euc-kr', 'latin-1']
            content = None
            used_encoding = None

            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as file:
                        content = file.read()
                        used_encoding = encoding
                        break
                except UnicodeDecodeError:
                    continue

            if content is None:
                # 모든 인코딩 실패 시 바이너리 모드로 읽기
                with open(file_path, 'rb') as file:
                    raw_content = file.read()
                    # UTF-8로 강제 디코딩
                    content = raw_content.decode('utf-8', errors='replace')
                    used_encoding = 'utf-8 (errors=replace)'
            
            logger.info(f"TXT 파일 처리 완료: {file_path}, 인코딩: {used_encoding}")
            
            return {
                "content": content,
                "metadata": {
                    "file_type": "txt",
                    "encoding": used_encoding,
                }
            }
            
        except Exception as e:
            logger.error(f"TXT 처리 실패: {file_path}, 오류: {e}", exc_info=True)
            raise