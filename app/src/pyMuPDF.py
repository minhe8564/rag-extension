from .base import BaseExtractionStrategy
from typing import Dict, Any
from loguru import logger

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
            for page_num in range(total_pages):
                page = doc[page_num]
                text = page.get_text()
                text_content.append({
                    "page": page_num + 1,
                    "content": text
                })
            
            # 전체 텍스트 합치기
            full_text = "\n".join([page["content"] for page in text_content])
            
            doc.close()
            
            return {
                "type": "pdf",
                "content": full_text,
                "pages": text_content,
                "total_pages": total_pages,
                "strategy": "basic",
                "parameters": self.parameters,
                "length": len(full_text)
            }
        except Exception as e:
            logger.error(f"[BasicPdf] Error extracting PDF: {str(e)}")
            raise
