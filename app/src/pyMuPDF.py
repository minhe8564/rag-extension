from .base import BaseExtractionStrategy
from typing import Dict, Any
from loguru import logger
import os
from app.service.minio_client import ensure_bucket, put_object_bytes

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None
    logger.warning("PyMuPDF not installed. PDF extraction will not work.")


class PyMuPDF(BaseExtractionStrategy):
    """Basic PDF 추출 전략 - PyMuPDF 사용"""
    
    def extract(self, file_path: str) -> Dict[Any, Any]:
        """PDF 파일 추출 처리"""
        logger.info(f"[BasicPdf] Extracting PDF file: {file_path}")

        if fitz is None:
            raise ImportError("PyMuPDF is required for PDF extraction. Install it with: pip install PyMuPDF")

        try:
            # PDF 문서 열기
            doc = fitz.open(file_path)
            total_pages = len(doc)

            # 전체 텍스트 추출
            text_content = []
            # 진행률 콜백 (옵션)
            progress_cb = None
            try:
                progress_cb = self.parameters.get("progress_cb") if isinstance(self.parameters, dict) else None
            except Exception:
                progress_cb = None

            processed = 0
            if progress_cb and total_pages:
                try:
                    progress_cb(processed, total_pages)
                except Exception:
                    pass
            for page_num in range(total_pages):
                page = doc[page_num]
                text = page.get_text()
                text_content.append({
                    "page": page_num + 1,
                    "content": text
                })
                processed += 1
                if progress_cb:
                    try:
                        progress_cb(processed, total_pages)
                    except Exception:
                        pass
            # 전체 텍스트 합치기
            full_text = "\n".join([page["content"] for page in text_content])
            doc.close()
            
            # MinIO 업로드
            try:
                user_id = (self.parameters.get("user_id") or "unknown-user") if isinstance(self.parameters, dict) else "unknown-user"
                file_name = (self.parameters.get("file_name") or "extracted.pdf") if isinstance(self.parameters, dict) else "extracted.pdf"
                base_name = os.path.splitext(file_name)[0] or "extracted"
                object_name = f"{user_id}/{base_name}.txt"
                bucket = "ingest"
                ensure_bucket(bucket)
                put_object_bytes(bucket, object_name, full_text.encode("utf-8"), content_type="text/plain; charset=utf-8")
                return {"full_text": full_text, "bucket": bucket, "path": object_name}
            except Exception as e:
                logger.warning(f"[BasicPdf] MinIO upload failed: {e}")
                return {"full_text": full_text}
        except Exception as e:
            logger.error(f"[BasicPdf] Error extracting PDF: {str(e)}")
            raise
