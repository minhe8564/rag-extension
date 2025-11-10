from .base import BaseExtractionStrategy
from typing import Dict, Any
from loguru import logger

try:
    from docx import Document
except ImportError:
    Document = None
    logger.warning("python-docx not installed. DOCX extraction will not work.")


class Docx(BaseExtractionStrategy):
    """Basic DOCX 추출 전략 - python-docx 사용"""
    
    def extract(self, file_path: str) -> Dict[Any, Any]:
        """DOCX 파일 추출 처리"""
        logger.info(f"[BasicDocs] Extracting DOCX file: {file_path}")
        
        if Document is None:
            raise ImportError("python-docx is required for DOCX extraction. Install it with: pip install python-docx")
        
        try:
            # DOCX 문서 열기
            doc = Document(file_path)
            
            # 전체 텍스트 추출
            paragraphs = []
            for para in doc.paragraphs:
                if para.text.strip():  # 빈 문단 제외
                    paragraphs.append(para.text)
            
            # 표에서 텍스트 추출
            tables_text = []
            for table in doc.tables:
                table_rows = []
                for row in table.rows:
                    row_cells = []
                    for cell in row.cells:
                        row_cells.append(cell.text.strip())
                    table_rows.append(row_cells)
                tables_text.append(table_rows)
            
            # 전체 텍스트 합치기
            full_text = "\n".join(paragraphs)
            
            return {
                "type": "docs",
                "content": full_text,
                "paragraphs": paragraphs,
                "tables": tables_text,
                "strategy": "basic",
                "parameters": self.parameters,
                "paragraph_count": len(paragraphs),
                "table_count": len(tables_text),
                "length": len(full_text)
            }
        except Exception as e:
            logger.error(f"[BasicDocs] Error extracting DOCX: {str(e)}")
            raise

