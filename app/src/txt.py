from .base import BaseExtractionStrategy
from typing import Dict, Any
from loguru import logger


class Txt(BaseExtractionStrategy):
    """Basic TXT 추출 전략 - 파일을 그대로 읽어서 반환"""
    
    def extract(self, file_path: str) -> Dict[Any, Any]:
        """TXT 파일 추출 처리"""
        logger.info(f"[BasicTxt] Extracting TXT file: {file_path}")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return {
                "type": "txt",
                "content": content,
                "strategy": "basic",
                "parameters": self.parameters,
                "length": len(content)
            }
        except UnicodeDecodeError:
            # UTF-8 실패 시 다른 인코딩 시도
            logger.warning(f"[BasicTxt] UTF-8 decode failed, trying latin-1")
            with open(file_path, 'r', encoding='latin-1') as f:
                content = f.read()
            return {
                "type": "txt",
                "content": content,
                "strategy": "basic",
                "parameters": self.parameters,
                "length": len(content)
            }
        except Exception as e:
            logger.error(f"[BasicTxt] Error extracting TXT: {str(e)}")
            raise

