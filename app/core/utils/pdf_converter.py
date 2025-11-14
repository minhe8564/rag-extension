"""
PDF 변환 유틸리티
Word, Excel, PPT, HTML 파일을 PDF로 변환
플랫폼별로 다른 방법 사용:
- Windows: Office COM (Word/Excel/PPT만) > docx2pdf (Word만) > LibreOffice (모든 형식)
- Linux/Mac: LibreOffice (모든 형식)
"""
import logging
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def _convert_with_libreoffice(file_path: str, pdf_path: Path) -> str:
    """
    LibreOffice를 사용한 PDF 변환 (Linux/Mac)
    """
    cmd = [
        "libreoffice",
        "--headless",
        "--convert-to", "pdf",
        "--outdir", str(pdf_path.parent),
        str(file_path)
    ]
    
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=60
    )
    
    if result.returncode != 0:
        raise RuntimeError(f"LibreOffice 변환 실패: {result.stderr}")
    
    expected_pdf = pdf_path.parent / f"{Path(file_path).stem}.pdf"
    if expected_pdf.exists():
        logger.info(f"PDF 변환 성공 (LibreOffice): {file_path} -> {expected_pdf}")
        return str(expected_pdf)
    else:
        raise RuntimeError(f"PDF 파일이 생성되지 않았습니다: {expected_pdf}")


def _convert_with_docx2pdf(file_path: str, pdf_path: Path) -> str:
    """
    docx2pdf를 사용한 PDF 변환 (Windows, Word만)
    """
    try:
        from docx2pdf import convert
        
        # docx2pdf는 출력 경로를 직접 지정
        convert(str(file_path), str(pdf_path))
        
        if pdf_path.exists():
            logger.info(f"PDF 변환 성공 (docx2pdf): {file_path} -> {pdf_path}")
            return str(pdf_path)
        else:
            raise RuntimeError(f"PDF 파일이 생성되지 않았습니다: {pdf_path}")
    except ImportError:
        raise RuntimeError("docx2pdf 라이브러리가 설치되어 있지 않습니다. pip install docx2pdf")
    except Exception as e:
        raise RuntimeError(f"docx2pdf 변환 실패: {str(e)}")


def _convert_with_office_com(file_path: str, pdf_path: Path) -> str:
    """
    Microsoft Office COM 객체를 사용한 PDF 변환 (Windows)
    """
    try:
        import win32com.client
        
        file_ext = Path(file_path).suffix.lower()
        file_path_resolved = str(Path(file_path).resolve())
        pdf_path_resolved = str(pdf_path.resolve())
        
        if file_ext == ".docx":
            app = win32com.client.Dispatch("Word.Application")
            app.Visible = False
            try:
                doc = app.Documents.Open(file_path_resolved)
                doc.SaveAs2(
                    pdf_path_resolved,
                    FileFormat=17  # wdFormatPDF = 17
                )
                doc.Close()
                logger.info(f"PDF 변환 성공 (Word COM): {file_path} -> {pdf_path}")
                return pdf_path_resolved
            finally:
                app.Quit()
        elif file_ext in [".xlsx", ".xls"]:
            app = win32com.client.Dispatch("Excel.Application")
            app.Visible = False
            try:
                wb = app.Workbooks.Open(file_path_resolved)
                wb.ExportAsFixedFormat(
                    Type=0,  # xlTypePDF = 0
                    Filename=pdf_path_resolved,
                    Quality=0,  # xlQualityStandard = 0
                    IncludeDocProperties=True,
                    IgnorePrintAreas=False,
                    OpenAfterPublish=False
                )
                wb.Close(False)
                logger.info(f"PDF 변환 성공 (Excel COM): {file_path} -> {pdf_path}")
                return pdf_path_resolved
            finally:
                app.Quit()
        elif file_ext in [".pptx", ".ppt"]:
            # PowerPoint는 Visible 속성을 지원하지 않음 (설정하지 않음)
            app = win32com.client.Dispatch("PowerPoint.Application")
            app.DisplayAlerts = 1  # ppAlertsNone = 1 (알림 숨기기)
            try:
                # WithWindow=False로 창을 숨김
                presentation = app.Presentations.Open(
                    file_path_resolved,
                    WithWindow=False,
                    ReadOnly=True
                )
                presentation.SaveAs(
                    pdf_path_resolved,
                    FileFormat=32  # ppSaveAsPDF = 32
                )
                presentation.Close()
                logger.info(f"PDF 변환 성공 (PowerPoint COM): {file_path} -> {pdf_path}")
                return pdf_path_resolved
            finally:
                app.Quit()
        else:
            raise RuntimeError(f"지원하지 않는 파일 형식: {file_ext}")
            
    except ImportError:
        raise RuntimeError("pywin32가 설치되어 있지 않습니다. pip install pywin32")
    except Exception as e:
        raise RuntimeError(f"Office COM 변환 실패: {str(e)}")


def convert_to_pdf(file_path: str, output_dir: Optional[str] = None) -> str:
    """
    Word/Excel/PPT/HTML 파일을 PDF로 변환
    플랫폼별로 다른 방법 사용:
    - Windows: Office COM (Word/Excel/PPT만) > docx2pdf (Word만) > LibreOffice (모든 형식)
    - Linux/Mac: LibreOffice (모든 형식)
    
    Args:
        file_path: 변환할 파일 경로
        output_dir: 출력 디렉토리 (None이면 임시 디렉토리 사용)
    
    Returns:
        생성된 PDF 파일 경로
    
    Raises:
        RuntimeError: 변환 실패 시
    """
    file_path_obj = Path(file_path)
    if not file_path_obj.exists():
        raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")
    
    file_ext = file_path_obj.suffix.lower()
    
    # 출력 디렉토리 설정
    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        pdf_path = output_path / f"{file_path_obj.stem}.pdf"
    else:
        temp_dir = Path(tempfile.gettempdir())
        pdf_path = temp_dir / f"{file_path_obj.stem}_{file_ext[1:]}.pdf"
    
    # Windows인 경우
    if sys.platform == "win32":
        # 방법 1: Office COM 객체 시도 (Word/Excel/PPT만)
        if file_ext in [".docx", ".xlsx", ".xls", ".pptx", ".ppt"]:  # 🔧 PPT 추가
            try:
                return _convert_with_office_com(file_path, pdf_path)
            except Exception as e:
                logger.warning(f"Office COM 변환 실패, 다른 방법 시도: {e}")
        
        # 방법 2: docx2pdf 시도 (Word만)
        if file_ext == ".docx":
            try:
                return _convert_with_docx2pdf(file_path, pdf_path)
            except Exception as e:
                logger.warning(f"docx2pdf 변환 실패, LibreOffice 시도: {e}")
        
        # 방법 3: LibreOffice 시도 (모든 형식)
        try:
            return _convert_with_libreoffice(file_path, pdf_path)
        except FileNotFoundError:
            error_msg = (
                "PDF 변환 도구를 찾을 수 없습니다.\n"
                "다음 중 하나를 설치하세요:\n"
                "1. Microsoft Office (Word/Excel) - 권장\n"
                "2. LibreOffice (https://www.libreoffice.org/download/)\n"
                "3. docx2pdf (pip install docx2pdf) - Word만"
            )
            raise RuntimeError(error_msg)
        except Exception as e:
            raise RuntimeError(f"PDF 변환 실패: {str(e)}")
    
    # Linux/Mac인 경우
    else:
        try:
            return _convert_with_libreoffice(file_path, pdf_path)
        except FileNotFoundError:
            raise RuntimeError(
                "LibreOffice가 설치되어 있지 않습니다. "
                "설치 방법: sudo apt-get install libreoffice (Ubuntu/Debian) "
                "또는 brew install libreoffice (Mac)"
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError("PDF 변환 시간 초과")
        except Exception as e:
            logger.error(f"PDF 변환 실패: {e}", exc_info=True)
            raise RuntimeError(f"PDF 변환 중 오류 발생: {str(e)}")
