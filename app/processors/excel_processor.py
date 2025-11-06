"""
Excel 프로세서
Excel 파일(.xlsx, .xls)을 Markdown으로 변환
"""
import logging
from pathlib import Path
from typing import Dict, Any, List

import pandas as pd
from xlrd.biffh import XLRDError
from openpyxl.utils.exceptions import InvalidFileException
from zipfile import BadZipFile

from .base import BaseProcessor

logger = logging.getLogger(__name__)


class ExcelProcessor(BaseProcessor):
    """
    Excel 파일(.xlsx, .xls)을 Markdown으로 변환하는 프로세서
    """
    
    @property
    def supported_extensions(self) -> List[str]:
        """
        지원하는 파일 확장자
        """
        return [".xlsx", ".xls"]
    
    def _dataframe_to_markdown(self, df: pd.DataFrame, sheet_name: str = None) -> str:
        """
        DataFrame을 Markdown 테이블 형식으로 변환
        """
        if df.empty:
            return f"## {sheet_name or 'Sheet'}\n\n(빈 시트)\n\n"
        
        # DataFrame to Markdown table
        md_table = df.to_markdown(index=False, tablefmt="pipe")
        
        if sheet_name:
            return f"## {sheet_name}\n\n{md_table}\n\n"
        else:
            return f"{md_table}\n\n"
    
    def _is_protected_file_error(self, error: Exception) -> bool:
        """
        보호된 파일 관련 오류인지 확인
        """
        error_str = str(error).lower()
        error_type = type(error).__name__
        
        # 보호된 파일 관련 오류 패턴
        protected_patterns = [
            "can't find workbook",
            "ole2 compound document",
            "password",
            "protected",
            "encrypted",
            "locked",
            "permission denied",
            "decrypt",
        ]
        
        return any(pattern in error_str for pattern in protected_patterns) or \
               error_type in ['XLRDError', 'BadZipFile', 'InvalidFileException', 'PermissionError']
    
    def process(self, file_path: str) -> Dict[str, Any]:
        """
        Excel 파일 -> Markdown 변환
        """
        if not Path(file_path).exists():
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")
        
        try:
            # Excel 파일 읽기 시도
            excel_file = pd.ExcelFile(file_path)
            sheet_names = excel_file.sheet_names
            
            logger.info(f"Excel 파일 처리 시작: {file_path}, 시트 수: {len(sheet_names)}")
            
            markdown_parts = []
            sheets_info = []
            
            # 각 시트 처리
            for sheet_name in sheet_names:
                try:
                    df = pd.read_excel(excel_file, sheet_name=sheet_name)
                    
                    # Markdown 변환
                    md_content = self._dataframe_to_markdown(df, sheet_name)
                    markdown_parts.append(md_content)
                    
                    sheets_info.append({
                        "name": sheet_name,
                        "rows": len(df),
                        "columns": len(df.columns),
                        "column_names": list(df.columns)
                    })
                    
                    logger.info(f"시트 '{sheet_name}' 처리 완료: {len(df)}행, {len(df.columns)}열")
                    
                except Exception as e:
                    # 보호된 시트 오류 확인
                    if self._is_protected_file_error(e):
                        error_msg = f"시트 '{sheet_name}'가 보호되어 있어 읽을 수 없습니다. 비밀번호를 제거하거나 보호를 해제한 후 다시 시도해주세요."
                        logger.warning(f"보호된 시트: {sheet_name}, 오류: {e}")
                        markdown_parts.append(f"## {sheet_name}\n\n⚠️ {error_msg}\n\n")
                    else:
                        logger.warning(f"시트 처리 실패: {sheet_name}, 오류: {e}")
                        markdown_parts.append(f"## {sheet_name}\n\n(시트 처리 중 오류 발생: {str(e)})\n\n")
            
            # 전체 Markdown 합치기
            full_markdown = "\n".join(markdown_parts)
            
            logger.info(f"Excel 파일 처리 완료: {file_path}")
            
            return {
                "content": full_markdown,
                "metadata": {
                    "file_type": Path(file_path).suffix.lower(),
                    "sheet_count": len(sheet_names),
                    "sheets": sheets_info,
                }
            }
            
        except XLRDError as e:
            # xlrd 관련 오류 (보호된 .xls 파일 등)
            error_str = str(e).lower()
            if "can't find workbook" in error_str or "ole2" in error_str:
                error_msg = "Excel 파일이 보호되어 있거나 손상되었습니다. 파일이 비밀번호로 보호되어 있는지 확인하고, 보호를 해제한 후 다시 시도해주세요."
            else:
                error_msg = f"Excel 파일 읽기 실패: {str(e)}"
            logger.error(f"Excel 파일 읽기 실패 (XLRDError): {file_path}, 오류: {e}")
            raise ValueError(error_msg)
            
        except BadZipFile as e:
            error_msg = "Excel 파일이 손상되었거나 보호되어 있습니다. 파일이 비밀번호로 보호되어 있는지 확인해주세요."
            logger.error(f"Excel 파일 읽기 실패 (BadZipFile): {file_path}, 오류: {e}")
            raise ValueError(error_msg)
            
        except InvalidFileException as e:
            error_msg = "Excel 파일이 보호되어 있거나 유효하지 않은 형식입니다. 비밀번호를 제거하거나 보호를 해제한 후 다시 시도해주세요."
            logger.error(f"Excel 파일 읽기 실패 (InvalidFileException): {file_path}, 오류: {e}")
            raise ValueError(error_msg)
            
        except PermissionError as e:
            error_msg = "Excel 파일에 접근할 수 없습니다. 파일이 다른 프로그램에서 열려있거나 권한이 없습니다."
            logger.error(f"Excel 파일 접근 실패 (PermissionError): {file_path}, 오류: {e}")
            raise ValueError(error_msg)
            
        except Exception as e:
            # 보호된 파일 오류 확인
            if self._is_protected_file_error(e):
                error_msg = "Excel 파일이 보호되어 있어 읽을 수 없습니다. 비밀번호를 제거하거나 보호를 해제한 후 다시 시도해주세요."
                logger.error(f"보호된 Excel 파일: {file_path}, 오류: {e}")
                raise ValueError(error_msg)
            else:
                logger.error(f"Excel 처리 실패: {file_path}, 오류: {e}", exc_info=True)
                raise