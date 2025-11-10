from .base import BaseExtractionStrategy
from typing import Dict, Any, List
from loguru import logger

try:
    from openpyxl import load_workbook
except ImportError:
    load_workbook = None
    logger.warning("openpyxl not installed. XLSX extraction will not work.")


class Openpyxl(BaseExtractionStrategy):
    """Basic XLSX 추출 전략 - openpyxl 사용"""
    
    def extract(self, file_path: str) -> Dict[Any, Any]:
        """XLSX 파일 추출 처리"""
        logger.info(f"[BasicXlsx] Extracting XLSX file: {file_path}")
        
        if load_workbook is None:
            raise ImportError("openpyxl is required for XLSX extraction. Install it with: pip install openpyxl")
        
        try:
            # XLSX 파일 열기
            workbook = load_workbook(file_path, data_only=True)
            
            # 모든 시트 데이터 추출
            sheets_data = {}
            sheets_text = []
            
            for sheet_name in workbook.sheetnames:
                sheet = workbook[sheet_name]
                
                # 시트의 모든 셀 데이터 추출
                sheet_rows = []
                sheet_text_rows = []
                
                for row in sheet.iter_rows(values_only=True):
                    # None 값을 빈 문자열로 변환
                    row_data = [str(cell) if cell is not None else "" for cell in row]
                    sheet_rows.append(row_data)
                    
                    # 텍스트로 합치기 (탭으로 구분)
                    row_text = "\t".join([str(cell) if cell is not None else "" for cell in row])
                    sheet_text_rows.append(row_text)
                
                sheets_data[sheet_name] = {
                    "rows": sheet_rows,
                    "row_count": len(sheet_rows)
                }
                
                # 시트별 텍스트 합치기
                sheet_text = "\n".join(sheet_text_rows)
                sheets_text.append({
                    "sheet_name": sheet_name,
                    "content": sheet_text
                })
            
            workbook.close()
            
            # 전체 텍스트 합치기
            full_text = "\n\n".join([sheet["content"] for sheet in sheets_text])
            
            return {
                "type": "xlsx",
                "content": full_text,
                "sheets": sheets_data,
                "sheets_text": sheets_text,
                "sheet_names": workbook.sheetnames,
                "sheet_count": len(workbook.sheetnames),
                "strategy": "basic",
                "parameters": self.parameters,
                "length": len(full_text)
            }
        except Exception as e:
            logger.error(f"[BasicXlsx] Error extracting XLSX: {str(e)}")
            raise

