from .base import BaseExtractionStrategy
from typing import Dict, Any
from loguru import logger


class Txt(BaseExtractionStrategy):
    """Basic TXT 추출 전략 - 파일을 그대로 읽어서 반환"""
    
    def extract(self, file_path: str) -> Dict[Any, Any]:
        """TXT 파일 추출 처리"""
        logger.info(f"[BasicTxt] Extracting TXT file: {file_path}")
        # 진행률 콜백 (옵션)
        progress_cb = None
        try:
            progress_cb = self.parameters.get("progress_cb") if isinstance(self.parameters, dict) else None
        except Exception:
            progress_cb = None

        def _read_with_encoding(enc: str) -> str:
            with open(file_path, 'r', encoding=enc) as f:
                if progress_cb:
                    try:
                        import os
                        total_bytes = os.path.getsize(file_path)
                    except Exception:
                        total_bytes = 0
                    processed_bytes = 0
                    if total_bytes:
                        try:
                            progress_cb(0, total_bytes)
                        except Exception:
                            pass
                    chunks = []
                    chunk_size = 64 * 1024
                    while True:
                        chunk = f.read(chunk_size)
                        if not chunk:
                            break
                        chunks.append(chunk)
                        processed_bytes += len(chunk.encode(enc, errors="ignore"))
                        if total_bytes:
                            try:
                                progress_cb(processed_bytes, total_bytes)
                            except Exception:
                                pass
                    return "".join(chunks)
                else:
                    return f.read()

        try:
            content = _read_with_encoding('utf-8')
        except UnicodeDecodeError:
            logger.warning(f"[BasicTxt] UTF-8 decode failed, trying latin-1")
            content = _read_with_encoding('latin-1')
        except Exception as e:
            logger.error(f"[BasicTxt] Error extracting TXT: {str(e)}")
            raise

        return {
            "type": "txt",
            "content": content,
            "strategy": "basic",
            "parameters": self.parameters,
            "length": len(content)
        }



