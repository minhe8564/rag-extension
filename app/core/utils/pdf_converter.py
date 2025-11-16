"""
PDF 변환 유틸리티
Word, Excel, PPT, HTML 파일을 PDF로 변환
"""
import logging
import re
import subprocess
import sys
import tempfile
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.request import urlretrieve

from app.core.settings import settings

logger = logging.getLogger(__name__)


def _find_libreoffice_command() -> str:
    """
    LibreOffice 실행 파일 경로 찾기
    Mac에서는 brew로 설치한 경우 일반적인 경로를 확인
    """
    # 먼저 일반적인 명령어로 시도
    import shutil
    if shutil.which("libreoffice"):
        return "libreoffice"
    if shutil.which("soffice"):
        return "soffice"
    
    # Mac에서 brew로 설치한 경우 일반적인 경로들
    if sys.platform == "darwin":
        possible_paths = [
            "/Applications/LibreOffice.app/Contents/MacOS/soffice",
            "/opt/homebrew/bin/libreoffice",
            "/usr/local/bin/libreoffice",
            "/opt/homebrew/Caskroom/libreoffice/stable/LibreOffice.app/Contents/MacOS/soffice",
        ]
        
        for path in possible_paths:
            if Path(path).exists():
                logger.info(f"LibreOffice 경로 발견: {path}")
                return path
    
    # 찾지 못한 경우 기본값 반환 (에러는 나중에 발생)
    return "libreoffice"


def _prepare_html_for_conversion(html_path: str) -> str:
    """
    HTML 파일을 PDF 변환을 위해 준비
    - 상대 경로 이미지를 절대 경로로 변환
    - 외부 URL 이미지를 다운로드하여 로컬 파일로 변환
    
    Args:
        html_path: HTML 파일 경로
    
    Returns:
        처리된 HTML 파일 경로 (원본 또는 임시 파일)
    """
    html_file = Path(html_path)
    if not html_file.exists():
        raise FileNotFoundError(f"HTML 파일을 찾을 수 없습니다: {html_path}")
    
    html_dir = html_file.parent
    html_content = html_file.read_text(encoding='utf-8', errors='ignore')
    
    # 다운로드한 이미지 파일을 저장할 임시 디렉토리
    temp_img_dir = Path(tempfile.mkdtemp(prefix='html_images_'))
    downloaded_images = {}  # URL -> 로컬 경로 매핑
    
    def download_image(url: str) -> Optional[str]:
        """외부 URL 이미지를 다운로드하여 로컬 파일로 저장"""
        if url in downloaded_images:
            return downloaded_images[url]
        
        try:
            # URL에서 파일 확장자 추출
            parsed_url = urllib.parse.urlparse(url)
            path = parsed_url.path
            ext = Path(path).suffix or '.jpg'  # 확장자가 없으면 기본값
            
            # 안전한 파일명 생성
            safe_filename = f"img_{len(downloaded_images)}{ext}"
            local_path = temp_img_dir / safe_filename
            
            # 이미지 다운로드
            urlretrieve(url, str(local_path))
            
            if local_path.exists():
                downloaded_images[url] = str(local_path.resolve())
                logger.info(f"외부 이미지 다운로드 완료: {url} -> {local_path}")
                return downloaded_images[url]
        except Exception as e:
            logger.warning(f"외부 이미지 다운로드 실패: {url}, 오류: {e}")
        
        return None
    
    # 이미지 태그 찾기 (img, source 등)
    img_pattern = r'(<img[^>]+src=["\'])([^"\']+)(["\'][^>]*>)'
    source_pattern = r'(<source[^>]+src=["\'])([^"\']+)(["\'][^>]*>)'
    
    modified = False
    
    def replace_image_path(match):
        nonlocal modified
        prefix = match.group(1)
        img_path = match.group(2)
        suffix = match.group(3)
        
        # data URI는 그대로 유지 (이미 인라인으로 포함되어 있음)
        if img_path.startswith('data:'):
            return match.group(0)
        
        # 외부 URL 이미지 다운로드
        if img_path.startswith('http://') or img_path.startswith('https://'):
            local_path = download_image(img_path)
            if local_path:
                modified = True
                return f"{prefix}{local_path}{suffix}"
            # 다운로드 실패 시 원본 유지
            return match.group(0)
        
        # 절대 경로인 경우 그대로 유지
        if Path(img_path).is_absolute():
            if Path(img_path).exists():
                return match.group(0)
            logger.warning(f"이미지 파일을 찾을 수 없습니다: {img_path}")
            return match.group(0)
        
        # 상대 경로를 절대 경로로 변환
        abs_path = (html_dir / img_path).resolve()
        if abs_path.exists():
            modified = True
            return f"{prefix}{abs_path}{suffix}"
        
        # 파일이 없으면 원본 유지
        logger.warning(f"이미지 파일을 찾을 수 없습니다: {img_path}")
        return match.group(0)
    
    # img 태그 처리
    html_content = re.sub(img_pattern, replace_image_path, html_content, flags=re.IGNORECASE)
    
    # source 태그 처리
    html_content = re.sub(source_pattern, replace_image_path, html_content, flags=re.IGNORECASE)
    
    # CSS background-image도 처리
    bg_pattern = r'(background-image:\s*url\(["\']?)([^"\'()]+)(["\']?\))'
    
    def replace_bg_image(match):
        nonlocal modified
        prefix = match.group(1)
        img_path = match.group(2)
        suffix = match.group(3)
        
        # data URI는 그대로 유지
        if img_path.startswith('data:'):
            return match.group(0)
        
        # 외부 URL 이미지 다운로드
        if img_path.startswith('http://') or img_path.startswith('https://'):
            local_path = download_image(img_path)
            if local_path:
                modified = True
                return f"{prefix}{local_path}{suffix}"
            # 다운로드 실패 시 원본 유지
            return match.group(0)
        
        # 절대 경로인 경우 그대로 유지
        if Path(img_path).is_absolute():
            if Path(img_path).exists():
                return match.group(0)
            return match.group(0)
        
        # 상대 경로를 절대 경로로 변환
        abs_path = (html_dir / img_path).resolve()
        if abs_path.exists():
            modified = True
            return f"{prefix}{abs_path}{suffix}"
        
        return match.group(0)
    
    html_content = re.sub(bg_pattern, replace_bg_image, html_content, flags=re.IGNORECASE)
    
    # 수정된 경우 또는 이미지를 다운로드한 경우 임시 파일로 저장
    if modified or downloaded_images:
        temp_html = tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.html',
            delete=False,
            encoding='utf-8'
        )
        temp_html.write(html_content)
        temp_html.close()
        logger.info(f"HTML 파일 이미지 경로 처리 완료: {temp_html.name} (다운로드된 이미지: {len(downloaded_images)}개)")
        return temp_html.name
    
    # 수정되지 않은 경우 원본 반환
    return str(html_file)


def _convert_excel_with_dataframe(file_path: str, pdf_path: Path, original_file_path: Optional[str] = None) -> str:
    """
    Excel 파일을 pandas DataFrame으로 읽어서 각 셀 데이터를 출력하고,
    각 셀을 별도 페이지로 직접 PDF로 변환 (reportlab 사용)
    
    Args:
        file_path: 변환할 Excel 파일 경로 (전치된 파일일 수 있음)
        pdf_path: 출력 PDF 파일 경로
        original_file_path: 원본 Excel 파일 경로 (이미지 추출용, 전치된 파일인 경우 제공)
    """
    import pandas as pd
    
    file_path_resolved = Path(file_path).resolve()
    pdf_path_resolved = pdf_path.resolve()
    
    # 원본 파일 경로 설정 (전치된 파일인 경우 원본에서 이미지 추출)
    image_source_path = file_path_resolved
    if original_file_path:
        image_source_path = Path(original_file_path).resolve()
        logger.info(f"Excel 파일을 DataFrame으로 읽기 시작: {file_path_resolved} (원본: {image_source_path})")
    else:
        logger.info(f"Excel 파일을 DataFrame으로 읽기 시작: {file_path_resolved}")
    
    # Excel 파일 읽기 (모든 시트)
    excel_file = pd.ExcelFile(file_path_resolved)
    
    logger.info(f"시트 수: {len(excel_file.sheet_names)}, 시트 이름: {', '.join(excel_file.sheet_names)}")
    
    # 모든 시트의 데이터와 이미지를 수집
    all_sheets_data = {}
    all_sheets_images = {}  # {sheet_name: {(row, col): image_path}}
    
    # 이미지 위치를 추적하여 최대 행/열 확인
    max_row_per_sheet = {}  # {sheet_name: max_row}
    max_col_per_sheet = {}  # {sheet_name: max_col}
    
    # openpyxl로 이미지 추출 시도
    try:
        import openpyxl
        from openpyxl.drawing.image import Image as OpenpyxlImage
        
        logger.info(f"Excel 이미지 추출 시작: {image_source_path}")
        
        wb = openpyxl.load_workbook(image_source_path)
        temp_image_dir = Path(tempfile.gettempdir()) / f"excel_images_{Path(image_source_path).stem}"
        temp_image_dir.mkdir(exist_ok=True)
        
        for sheet_name in wb.sheetnames:
            ws = wb[sheet_name]
            sheet_images = {}
            
            # 이미지 추출 (여러 방법 시도)
            images_found = []
            
            # 방법 1: _images 속성 확인
            if hasattr(ws, '_images') and ws._images:
                images_found = list(ws._images)
            
            # 방법 2: drawing 속성 확인
            if not images_found:
                try:
                    if hasattr(ws, 'drawings') and ws.drawings:
                        for drawing in ws.drawings:
                            if hasattr(drawing, '_images'):
                                images_found.extend(drawing._images)
                except Exception as e:
                    logger.debug(f"drawings 속성 접근 실패: {e}")
            
            # 방법 3: _rels를 통한 이미지 찾기
            if not images_found:
                try:
                    if hasattr(ws, '_rels'):
                        for rel in ws._rels.values():
                            if 'image' in str(rel.target) or 'drawing' in str(rel.target):
                                logger.debug(f"시트 '{sheet_name}': _rels에서 이미지 관계 발견: {rel.target}")
                except Exception as e:
                    logger.debug(f"_rels 접근 실패: {e}")
            
            # 방법 4: workbook의 _images 확인
            if not images_found:
                try:
                    if hasattr(wb, '_images') and wb._images:
                        images_found = list(wb._images)
                except Exception as e:
                    logger.debug(f"workbook._images 접근 실패: {e}")
            
            if images_found:
                logger.info(f"시트 '{sheet_name}': {len(images_found)}개 이미지 발견")
                
                for idx, img in enumerate(images_found):
                    try:
                        # 이미지 데이터 추출 (여러 방법 시도)
                        image_data = None
                        
                        # 방법 1: _data() 메서드
                        if hasattr(img, '_data'):
                            try:
                                if callable(img._data):
                                    image_data = img._data()
                                else:
                                    image_data = img._data
                                if image_data and isinstance(image_data, bytes):
                                    logger.debug(f"이미지 {idx+1}: _data() 메서드로 추출 성공, 크기: {len(image_data)} bytes")
                            except Exception as e:
                                logger.debug(f"이미지 {idx+1}: _data() 실패: {e}")
                        
                        # 방법 2: ref를 통한 이미지 파일 접근
                        if image_data is None and hasattr(img, 'ref'):
                            try:
                                ref = img.ref
                                # openpyxl의 내부 구조를 통해 이미지 찾기
                                if hasattr(wb, '_archive') and wb._archive:
                                    try:
                                        image_data = wb._archive.read(ref)
                                        if image_data:
                                            logger.debug(f"이미지 {idx+1}: ref를 통해 추출 성공, 크기: {len(image_data)} bytes")
                                    except Exception as e:
                                        logger.debug(f"이미지 {idx+1}: ref 접근 실패: {e}")
                            except Exception as e:
                                logger.debug(f"이미지 {idx+1}: ref 처리 실패: {e}")
                        
                        if image_data is None:
                            logger.warning(f"시트 '{sheet_name}' 이미지 {idx+1} 데이터 추출 실패")
                            continue
                        
                        # 이미지 형식 확인
                        if hasattr(img, 'format'):
                            ext = img.format.lower()
                        elif hasattr(img, 'ext'):
                            ext = img.ext.lower()
                        else:
                            # 이미지 데이터의 매직 넘버로 형식 확인
                            if image_data[:4] == b'\x89PNG':
                                ext = 'png'
                            elif image_data[:2] == b'\xff\xd8':
                                ext = 'jpg'
                            elif image_data[:6] in [b'GIF87a', b'GIF89a']:
                                ext = 'gif'
                            else:
                                ext = 'png'  # 기본값
                        
                        # 임시 이미지 파일 저장
                        image_path = temp_image_dir / f"{sheet_name}_img_{idx}.{ext}"
                        with open(image_path, 'wb') as f:
                            f.write(image_data)
                        
                        # 이미지 파일이 제대로 생성되었는지 확인
                        if not image_path.exists() or image_path.stat().st_size == 0:
                            logger.warning(f"이미지 파일 생성 실패: {image_path}")
                            continue
                        
                        # 이미지 위치 정보 (anchor를 사용하여 셀 위치 추정)
                        # 이미지는 여러 셀에 걸쳐 있을 수 있지만, 시작 셀에만 매핑
                        if hasattr(img, 'anchor') and img.anchor:
                            anchor = img.anchor
                            # anchor는 보통 셀 좌표를 포함
                            if hasattr(anchor, '_from'):
                                # 원본 파일의 좌표 (0-based)
                                orig_row = anchor._from.row + 1  # 0-based to 1-based
                                orig_col = anchor._from.col + 1
                                
                                # 전치된 파일인 경우 좌표 변환 (원본의 row, col -> 전치된 col, row)
                                if original_file_path:
                                    # 전치된 DataFrame에서는 원본의 열이 행이 되고, 원본의 행이 열이 됨
                                    # 원본 (row, col) -> 전치 (col, row)
                                    # 하지만 DataFrame을 읽을 때 이미 전치되어 있으므로, 
                                    # 원본의 (row, col)은 전치된 DataFrame의 (col, row)에 해당
                                    transposed_row = orig_col  # 원본의 열이 전치된 행
                                    transposed_col = orig_row  # 원본의 행이 전치된 열
                                    
                                    # 최대 행/열 추적 (DataFrame 확장용)
                                    if sheet_name not in max_row_per_sheet:
                                        max_row_per_sheet[sheet_name] = transposed_row
                                        max_col_per_sheet[sheet_name] = transposed_col
                                    else:
                                        max_row_per_sheet[sheet_name] = max(max_row_per_sheet[sheet_name], transposed_row)
                                        max_col_per_sheet[sheet_name] = max(max_col_per_sheet[sheet_name], transposed_col)
                                    
                                    # 좌표를 저장
                                    sheet_images[(transposed_row, transposed_col)] = str(image_path)
                                    logger.debug(f"이미지 {idx+1}: 원본 위치 [{orig_row},{orig_col}] -> 전치 위치 [{transposed_row},{transposed_col}] -> {image_path.name}")
                                else:
                                    # 전치되지 않은 경우 원본 좌표 그대로 사용
                                    sheet_images[(orig_row, orig_col)] = str(image_path)
                                    
                                    # 범위 정보는 로그에만 표시
                                    if hasattr(anchor, '_to') and hasattr(anchor._to, 'row') and hasattr(anchor._to, 'col'):
                                        to_row = anchor._to.row + 1
                                        to_col = anchor._to.col + 1
                                        if orig_row != to_row or orig_col != to_col:
                                            logger.debug(f"이미지 {idx+1}: 시작 위치 [{orig_row},{orig_col}] (범위: [{orig_row},{orig_col}]~[{to_row},{to_col}]) -> {image_path.name}")
                                        else:
                                            logger.debug(f"이미지 {idx+1}: 행 {orig_row}, 열 {orig_col} -> {image_path.name}")
                                    else:
                                        logger.debug(f"이미지 {idx+1}: 행 {orig_row}, 열 {orig_col} -> {image_path.name}")
                            else:
                                # anchor 정보가 없으면 첫 번째 셀에 배치
                                sheet_images[(1, 1)] = str(image_path)
                                logger.debug(f"이미지 {idx+1}: 위치 정보 없음 -> {image_path.name}")
                        else:
                            # anchor 정보가 없으면 첫 번째 셀에 배치
                            sheet_images[(1, 1)] = str(image_path)
                            logger.debug(f"이미지 {idx+1}: 위치 정보 없음 -> {image_path.name}")
                        
                        logger.info(f"시트 '{sheet_name}' 이미지 {idx+1} 추출: {image_path}")
                    except Exception as e:
                        logger.warning(f"시트 '{sheet_name}' 이미지 {idx+1} 추출 실패: {e}")
            
            all_sheets_images[sheet_name] = sheet_images
        
        wb.close()
        logger.info(f"Excel 이미지 추출 완료: 총 {sum(len(imgs) for imgs in all_sheets_images.values())}개 이미지")
        
    except ImportError:
        logger.debug("openpyxl이 설치되어 있지 않아 이미지 추출을 건너뜁니다")
    except Exception as e:
        logger.warning(f"Excel 이미지 추출 실패: {e}", exc_info=True)
    
    # 모든 시트의 데이터를 수집
    for sheet_name in excel_file.sheet_names:
        logger.info(f"시트 '{sheet_name}' 처리 시작")
        df = pd.read_excel(excel_file, sheet_name=sheet_name, header=None)
        
        # 이미지가 있는 경우 DataFrame을 이미지 위치까지 확장
        if sheet_name in max_row_per_sheet or sheet_name in max_col_per_sheet:
            required_rows = max_row_per_sheet.get(sheet_name, len(df))
            required_cols = max_col_per_sheet.get(sheet_name, len(df.columns))
            
            # 현재 DataFrame 크기
            current_rows = len(df)
            current_cols = len(df.columns)
            
            # 필요한 크기까지 확장
            if required_rows > current_rows or required_cols > current_cols:
                logger.info(f"시트 '{sheet_name}': DataFrame 확장 {current_rows}행 x {current_cols}열 -> {required_rows}행 x {required_cols}열")
                
                # 행 확장
                if required_rows > current_rows:
                    new_rows = pd.DataFrame([[None] * current_cols] * (required_rows - current_rows))
                    df = pd.concat([df, new_rows], ignore_index=True)
                
                # 열 확장
                if required_cols > current_cols:
                    for col_idx in range(current_cols, required_cols):
                        df[col_idx] = None
        
        logger.info(f"시트 '{sheet_name}': 행 수={len(df)}, 열 수={len(df.columns)}")
        
        # DataFrame 정보
        cell_count = sum(1 for row in range(len(df)) for col in range(len(df.columns)) if pd.notna(df.iloc[row, col]))
        logger.info(f"시트 '{sheet_name}': 총 {cell_count}개 셀에 데이터")
        
        all_sheets_data[sheet_name] = df
    
    # reportlab을 사용하여 직접 PDF 생성
    try:
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib.units import inch
        from reportlab.pdfgen import canvas
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import Paragraph, Spacer, PageBreak
        from reportlab.lib.enums import TA_LEFT, TA_CENTER
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        
        # PIL Image import
        try:
            from PIL import Image as PILImage
        except ImportError:
            try:
                import Image as PILImage
            except ImportError:
                logger.error("PIL/Pillow가 설치되어 있지 않습니다. 이미지 표시가 불가능합니다.")
                PILImage = None
        
        # PDF 생성
        c = canvas.Canvas(str(pdf_path_resolved), pagesize=landscape(A4))
        width, height = landscape(A4)
        
        # 한글 폰트 지원 시도 (시스템에 따라 다를 수 있음)
        font_name = 'Helvetica'  # 기본값
        try:
            import platform
            system = platform.system()
            
            if system == "Windows":
                # Windows: 맑은 고딕
                try:
                    pdfmetrics.registerFont(TTFont('MalgunGothic', 'C:/Windows/Fonts/malgun.ttf'))
                    font_name = 'MalgunGothic'
                    logger.debug("한글 폰트 등록: 맑은 고딕")
                except Exception as e:
                    logger.warning(f"맑은 고딕 폰트 등록 실패: {e}")
                    font_name = 'Helvetica'
            elif system == "Darwin":  # Mac
                # Mac: 시스템 폰트 경로에서 한글 폰트 찾기
                mac_font_paths = [
                    '/System/Library/Fonts/Supplemental/AppleGothic.ttf',
                    '/Library/Fonts/AppleGothic.ttf',
                    '/System/Library/Fonts/AppleGothic.ttf',
                    # 나눔고딕 (설치되어 있는 경우)
                    '/Library/Fonts/NanumGothic.ttf',
                    '~/Library/Fonts/NanumGothic.ttf',
                    # Arial Unicode MS
                    '/Library/Fonts/Arial Unicode.ttf',
                    '/System/Library/Fonts/Supplemental/Arial Unicode.ttf',
                ]
                
                for font_path in mac_font_paths:
                    expanded_path = Path(font_path).expanduser()
                    if expanded_path.exists():
                        try:
                            font_family = expanded_path.stem
                            pdfmetrics.registerFont(TTFont(font_family, str(expanded_path)))
                            font_name = font_family
                            logger.debug(f"한글 폰트 등록: {font_family} ({expanded_path})")
                            break
                        except Exception as e:
                            logger.debug(f"폰트 등록 실패 {expanded_path}: {e}")
                            continue
                
                if font_name == 'Helvetica':
                    logger.warning("Mac에서 한글 폰트를 찾을 수 없습니다. 기본 폰트 사용")
            else:  # Linux
                # Linux: 일반적인 한글 폰트 경로
                linux_font_paths = [
                    '/usr/share/fonts/truetype/nanum/NanumGothic.ttf',
                    '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
                    '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
                    '~/.fonts/NanumGothic.ttf',
                ]
                
                for font_path in linux_font_paths:
                    expanded_path = Path(font_path).expanduser()
                    if expanded_path.exists():
                        try:
                            font_family = expanded_path.stem
                            pdfmetrics.registerFont(TTFont(font_family, str(expanded_path)))
                            font_name = font_family
                            logger.debug(f"한글 폰트 등록: {font_family} ({expanded_path})")
                            break
                        except Exception as e:
                            logger.debug(f"폰트 등록 실패 {expanded_path}: {e}")
                            continue
                
                if font_name == 'Helvetica':
                    logger.warning("Linux에서 한글 폰트를 찾을 수 없습니다. 기본 폰트 사용")
        except Exception as e:
            logger.error(f"폰트 등록 중 오류: {e}", exc_info=True)
            font_name = 'Helvetica'
        
        total_cells = 0
        
        # 각 시트의 각 열을 별도 페이지로 생성 (한 열의 모든 행을 하나의 페이지에 표시)
        for sheet_name, df in all_sheets_data.items():
            sheet_images = all_sheets_images.get(sheet_name, {})
            
            # 이미지 매핑 정보 출력 및 범위 확인
            # 새로운 딕셔너리를 생성하여 범위를 벗어난 이미지 처리 (원본 딕셔너리 수정 방지)
            corrected_sheet_images = {}
            if sheet_images:
                for (img_row, img_col), img_path in sheet_images.items():
                    in_range = (1 <= img_row <= df.shape[0]) and (1 <= img_col <= df.shape[1])
                    
                    # 범위를 벗어난 이미지는 첫 번째 열에 배치
                    if not in_range:
                        if img_col > df.shape[1]:
                            # 열이 범위를 벗어나면 첫 번째 열에 배치
                            corrected_col = 1
                            corrected_row = min(img_row, df.shape[0]) if img_row > df.shape[0] else img_row
                            corrected_sheet_images[(corrected_row, corrected_col)] = img_path
                            logger.debug(f"이미지 재매핑: 행 {img_row}, 열 {img_col} -> 행 {corrected_row}, 열 {corrected_col}")
                        elif img_row > df.shape[0]:
                            # 행이 범위를 벗어나면 첫 번째 행에 배치
                            corrected_row = 1
                            corrected_col = min(img_col, df.shape[1]) if img_col > df.shape[1] else img_col
                            corrected_sheet_images[(corrected_row, corrected_col)] = img_path
                            logger.debug(f"이미지 재매핑: 행 {img_row}, 열 {img_col} -> 행 {corrected_row}, 열 {corrected_col}")
                    else:
                        # 범위 내 이미지는 그대로 사용
                        corrected_sheet_images[(img_row, img_col)] = img_path
                
                # 수정된 딕셔너리로 교체
                sheet_images = corrected_sheet_images
            
            # 각 열마다 하나의 페이지 생성
            for col_idx in range(len(df.columns)):
                col_data = df.iloc[:, col_idx]
                col_num = col_idx + 1  # 1-based
                
                # 열에 데이터가 있는지 확인 (모든 행 확인)
                has_data = False
                has_col_image = False
                col_cells = []
                col_images = []
                
                for row_idx in range(len(df)):
                    cell_value = col_data.iloc[row_idx]
                    row_num = row_idx + 1
                    
                    # 이미지 확인 (데이터보다 먼저 확인)
                    if (row_num, col_num) in sheet_images:
                        has_col_image = True
                        col_images.append((row_num, sheet_images[(row_num, col_num)]))
                        # 이미지가 있는 셀은 데이터가 없어도 포함 (이미지만 표시하기 위해)
                        if pd.isna(cell_value):
                            col_cells.append((row_num, ""))  # 빈 문자열로 추가
                    
                    if pd.notna(cell_value):
                        has_data = True
                        col_cells.append((row_num, str(cell_value)))
                
                # 열에 데이터나 이미지가 있으면 페이지 생성
                if has_data or has_col_image:
                    total_cells += 1
                    
                    # 첫 페이지가 아니면 새 페이지 시작
                    if total_cells > 1:
                        c.showPage()
                    # 첫 페이지는 이미 시작되어 있음
                    
                    # 헤더 (시트 이름, 열 번호)
                    header_text = f"시트: {sheet_name} | 열 {col_num}"
                    if has_col_image:
                        header_text += f" [이미지 {len(col_images)}개 포함]"
                    c.setFont(font_name, 14)
                    c.setFillColorRGB(0.4, 0.4, 0.4)
                    c.drawString(0.5*inch, height - 0.5*inch, header_text)
                    
                    # 구분선
                    c.setStrokeColorRGB(0.7, 0.7, 0.7)
                    c.line(0.5*inch, height - 0.6*inch, width - 0.5*inch, height - 0.6*inch)
                    
                    y_position = height - 1*inch
                    
                    # 각 행의 셀 내용 표시 (이미지는 해당 셀과 함께 표시)
                    c.setFont(font_name, 12)
                    c.setFillColorRGB(0, 0, 0)
                    line_height = 16
                    max_width = width - 1*inch
                    
                    for row_num, cell_str in col_cells:
                        # 해당 셀에 이미지가 있는지 확인
                        cell_image_path = None
                        if (row_num, col_num) in sheet_images:
                            cell_image_path = sheet_images[(row_num, col_num)]
                        
                        # 행 번호와 내용 표시
                        row_label = f"[행 {row_num}]"
                        c.setFont(font_name, 11)
                        c.setFillColorRGB(0.3, 0.3, 0.3)
                        c.drawString(0.5*inch, y_position, row_label)
                        y_position -= line_height
                        
                        # 해당 셀에 이미지가 있으면 먼저 이미지 표시
                        if cell_image_path:
                            try:
                                # 이미지 파일 존재 확인
                                image_path_obj = Path(cell_image_path)
                                if not image_path_obj.exists():
                                    logger.warning(f"이미지 파일이 존재하지 않음: {cell_image_path}")
                                elif PILImage is None:
                                    logger.warning("PIL/Pillow가 없어 이미지를 표시할 수 없음")
                                else:
                                    img = PILImage.open(cell_image_path)
                                    
                                    # 이미지 크기 조정 (페이지 너비에 맞게, 최대 높이 제한)
                                    img_max_width = width - 1*inch
                                    img_max_height = (height - 2*inch) / 4  # 셀당 이미지 공간
                                    
                                    img_width, img_height = img.size
                                    scale = min(img_max_width / img_width, img_max_height / img_height, 1.0)
                                    
                                    display_width = img_width * scale
                                    display_height = img_height * scale
                                    
                                    # 이미지 그리기 (셀 내용 위에 표시)
                                    img_x = 0.5*inch
                                    img_y = y_position - display_height
                                    
                                    # reportlab의 drawImage 사용 (절대 경로 사용)
                                    c.drawImage(str(image_path_obj.resolve()), img_x, img_y, 
                                              width=display_width, height=display_height, preserveAspectRatio=True)
                                    
                                    # 이미지 아래로 공간 확보
                                    y_position -= (display_height + 0.2*inch)
                            except Exception as e:
                                logger.error(f"이미지 표시 실패 [열 {col_num}, 행 {row_num}]: {e}", exc_info=True)
                        
                        # 셀 내용 표시
                        c.setFont(font_name, 12)
                        c.setFillColorRGB(0, 0, 0)
                        
                        # 텍스트를 여러 줄로 나누기
                        words = cell_str.split()
                        lines = []
                        current_line = ""
                        
                        for word in words:
                            test_line = current_line + (" " if current_line else "") + word
                            text_width = c.stringWidth(test_line, font_name, 12)
                            if text_width <= max_width:
                                current_line = test_line
                            else:
                                if current_line:
                                    lines.append(current_line)
                                    current_line = word
                                else:
                                    # 단어가 너무 길면 강제로 자름
                                    if len(word) > 100:
                                        word = word[:100] + "..."
                                    lines.append(word)
                        
                        if current_line:
                            lines.append(current_line)
                        
                        # 텍스트 출력 (최대 10줄)
                        max_lines_per_cell = 10
                        for i, line in enumerate(lines[:max_lines_per_cell]):
                            if y_position < 1.5*inch:
                                break
                            c.drawString(0.7*inch, y_position, line)
                            y_position -= line_height
                        
                        # 내용이 잘렸는지 표시
                        if len(lines) > max_lines_per_cell:
                            c.setFont(font_name, 10)
                            c.setFillColorRGB(0.5, 0.5, 0.5)
                            c.drawString(0.7*inch, y_position, f"... (내용이 길어 일부만 표시됨, 전체 길이: {len(cell_str)}자)")
                            y_position -= line_height
                        
                        # 셀 간 구분을 위한 공간
                        y_position -= 0.1*inch
                    
                    # 하단 정보
                    c.setFont(font_name, 10)
                    c.setFillColorRGB(0.6, 0.6, 0.6)
                    info_parts = [f"열 번호: {col_num}"]
                    if col_cells:
                        info_parts.append(f"셀 수: {len(col_cells)}개")
                    if has_col_image:
                        info_parts.append(f"이미지: {len(col_images)}개")
                    info_text = " | ".join(info_parts)
                    c.drawString(0.5*inch, 0.3*inch, info_text)
        
        # 마지막 페이지 저장
        c.save()
        
        logger.info(f"PDF 변환 성공 (DataFrame, reportlab, 각 열별 페이지): {file_path} -> {pdf_path}")
        return str(pdf_path_resolved)
        
    except ImportError:
        # reportlab이 없으면 HTML 방식으로 대체
        logger.warning("reportlab이 설치되어 있지 않아 HTML 방식으로 대체합니다.")
        return _convert_excel_with_dataframe_html(file_path, pdf_path)
    except Exception as e:
        logger.error(f"reportlab PDF 생성 실패: {e}, HTML 방식으로 대체")
        return _convert_excel_with_dataframe_html(file_path, pdf_path)


def _convert_excel_with_dataframe_html(file_path: str, pdf_path: Path) -> str:
    """
    Excel 파일을 pandas DataFrame으로 읽어서 각 셀을 별도 페이지로 HTML 변환 후 PDF로 변환
    (reportlab이 없을 때 사용하는 대체 방법)
    """
    import html as html_module
    import pandas as pd
    
    file_path_resolved = Path(file_path).resolve()
    pdf_path_resolved = pdf_path.resolve()
    
    # Excel 파일 읽기 (모든 시트)
    excel_file = pd.ExcelFile(file_path_resolved)
    
    # 모든 시트의 데이터를 수집
    all_sheets_data = {}
    for sheet_name in excel_file.sheet_names:
        df = pd.read_excel(excel_file, sheet_name=sheet_name, header=None)
        all_sheets_data[sheet_name] = df
    
    # HTML 생성 (각 셀을 별도 페이지로)
    html_content = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        @page {
            size: A4 landscape;
            margin: 0.5in;
        }
        body {
            font-family: 'Malgun Gothic', '맑은 고딕', Arial, sans-serif;
            margin: 0;
            padding: 0;
        }
        .cell-page {
            page-break-after: always;
            width: 100%;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            padding: 20px;
            box-sizing: border-box;
        }
        .cell-page:last-child {
            page-break-after: auto;
        }
        .cell-header {
            font-size: 14px;
            font-weight: bold;
            color: #666;
            margin-bottom: 10px;
            border-bottom: 2px solid #ddd;
            padding-bottom: 5px;
        }
        .cell-content {
            font-size: 12px;
            line-height: 1.6;
            white-space: pre-wrap;
            word-wrap: break-word;
            flex: 1;
            overflow: auto;
        }
        .cell-info {
            font-size: 10px;
            color: #999;
            margin-top: 10px;
            border-top: 1px solid #eee;
            padding-top: 5px;
        }
    </style>
</head>
<body>
"""
    
    # 각 시트의 각 셀을 별도 페이지로 생성
    total_cells = 0
    for sheet_name, df in all_sheets_data.items():
        for row_idx in range(len(df)):
            for col_idx in range(len(df.columns)):
                cell_value = df.iloc[row_idx, col_idx]
                
                # 셀이 비어있지 않은 경우만 페이지 생성
                if pd.notna(cell_value):
                    total_cells += 1
                    cell_str = str(cell_value)
                    
                    html_content += f"""
    <div class="cell-page">
        <div class="cell-header">
            시트: {sheet_name} | 위치: 행 {row_idx+1}, 열 {col_idx+1}
        </div>
        <div class="cell-content">
{html_module.escape(cell_str)}
        </div>
        <div class="cell-info">
            셀 주소: [{row_idx+1}, {col_idx+1}] | 길이: {len(cell_str)}자
        </div>
    </div>
"""
    
    html_content += """
</body>
</html>
"""
    
    # 임시 HTML 파일 저장
    temp_html = tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8')
    temp_html.write(html_content)
    temp_html.close()
    
    # HTML을 PDF로 변환 (Playwright 사용)
    pdf_result = _convert_with_playwright(temp_html.name, pdf_path_resolved)
    
    # 임시 HTML 파일 삭제
    try:
        Path(temp_html.name).unlink()
    except:
        pass
    logger.info(f"PDF 변환 성공 (DataFrame, HTML, 각 셀별 페이지): {file_path} -> {pdf_path}")
    return pdf_result


def _convert_with_playwright_sync(html_path: str, pdf_path: Path) -> str:
    """
    Playwright Sync API를 사용한 HTML to PDF 변환 (내부 함수)
    별도 스레드에서 실행되어야 함
    """
    from playwright.sync_api import sync_playwright
    
    html_file = Path(html_path)
    html_abs_path = html_file.resolve()
    
    # file:// 프로토콜로 로컬 파일 열기
    file_url = f"file://{html_abs_path}"
    
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=True)
        except Exception as browser_error:
            # 브라우저가 설치되지 않은 경우 자동 설치 시도
            if "Executable doesn't exist" in str(browser_error) or "Browser not found" in str(browser_error):
                logger.info("Chromium 브라우저가 설치되지 않았습니다. 자동 설치 시도...")
                import subprocess
                import sys
                # playwright install chromium 실행
                result = subprocess.run(
                    [sys.executable, "-m", "playwright", "install", "chromium"],
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                if result.returncode == 0:
                    logger.info("Chromium 브라우저 설치 완료")
                    browser = p.chromium.launch(headless=True)
                else:
                    raise RuntimeError(
                        f"Chromium 브라우저 자동 설치 실패: {result.stderr}\n"
                        f"수동 설치: playwright install chromium"
                    )
            else:
                raise
        
        page = browser.new_page()
        
        # 페이지 로드 (이미지 포함, 네트워크가 완전히 유휴 상태가 될 때까지 대기)
        page.goto(file_url, wait_until='networkidle', timeout=60000)
        
        # 이미지 로딩을 위한 추가 대기 (모든 이미지가 로드될 때까지)
        page.wait_for_load_state('networkidle')
        
        # 모든 이미지가 로드되었는지 확인
        images_loaded = page.evaluate("""
            () => {
                const images = Array.from(document.images);
                return images.every(img => img.complete && img.naturalHeight !== 0);
            }
        """)
        
        if not images_loaded:
            logger.warning("일부 이미지가 완전히 로드되지 않았을 수 있습니다. 추가 대기...")
            import time
            time.sleep(2)  # 추가 대기 시간
        
        # PDF로 저장 (이미지 품질 유지)
        page.pdf(
            path=str(pdf_path),
            format='A4',
            print_background=True,  # 배경 이미지 포함
            prefer_css_page_size=False,
            margin={
                'top': '0.5in',
                'right': '0.5in',
                'bottom': '0.5in',
                'left': '0.5in'
            }
        )
        
        browser.close()
    
    if pdf_path.exists():
        logger.info(f"PDF 변환 성공 (Playwright, 이미지 포함): {html_path} -> {pdf_path}")
        return str(pdf_path)
    else:
        raise RuntimeError(f"PDF 파일이 생성되지 않았습니다: {pdf_path}")


def _convert_with_playwright(html_path: str, pdf_path: Path) -> str:
    """
    Playwright를 사용한 HTML to PDF 변환 (브라우저 기반)
    이미지와 스타일이 완벽하게 렌더링됨
    모든 이미지(로컬, 외부 URL, data URI)가 포함됨
    
    asyncio 루프와의 충돌을 방지하기 위해 별도 스레드에서 실행
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise RuntimeError(
            "Playwright가 설치되어 있지 않습니다. "
            "설치 방법: uv sync (의존성 설치) && playwright install chromium"
        )
    
    # 별도 스레드에서 실행하여 asyncio 루프와의 충돌 방지
    try:
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_convert_with_playwright_sync, html_path, pdf_path)
            return future.result(timeout=120)  # 2분 타임아웃
    except Exception as e:
        raise RuntimeError(f"Playwright 변환 실패: {str(e)}")


def _convert_with_libreoffice(file_path: str, pdf_path: Path) -> str:
    """
    LibreOffice를 사용한 PDF 변환 (모든 플랫폼: Windows/Linux/Mac)
    이미지 품질 및 한글 폰트 유지를 위해 고품질 PDF 필터 옵션 사용
    모든 플랫폼에서 일관된 변환 품질 제공
    """
    # 이미지 품질 및 한글 폰트 유지를 위한 PDF 필터 옵션
    # LibreOffice 버전에 따라 일부 옵션이 지원되지 않을 수 있으므로 기본 옵션만 사용
    # Quality=100: 최고 품질
    # EmbedStandardFonts=1: 표준 폰트 임베드 (한글 폰트도 포함)
    # UseTaggedPDF=1: 태그된 PDF 사용 (이미지 포함)
    # MaxImageResolution=300: 최대 이미지 해상도 (DPI)
    # ReduceImageResolution=false: 이미지 해상도 축소 비활성화
    pdf_filter_options = "Quality=100,EmbedStandardFonts=1,UseTaggedPDF=1,MaxImageResolution=300,ReduceImageResolution=false"
    
    # LibreOffice 실행 파일 경로 찾기
    libreoffice_cmd = _find_libreoffice_command()
    
    # 입력 파일 경로를 절대 경로로 변환 (LibreOffice가 상대 경로를 제대로 처리하지 못할 수 있음)
    input_file = Path(file_path).resolve()
    output_dir = pdf_path.parent.resolve()
    
    # 출력 디렉토리 생성
    output_dir.mkdir(parents=True, exist_ok=True)
    
    cmd = [
        libreoffice_cmd,
        "--headless",
        "--nodefault",
        "--nolockcheck",
        "--convert-to", f"pdf:{pdf_filter_options}",
        "--outdir", str(output_dir),
        str(input_file)
    ]
    
    logger.debug(f"LibreOffice 명령어 실행: {' '.join(cmd)}")
    
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=120,  # 이미지가 많은 경우 시간이 더 걸릴 수 있음
        cwd=str(output_dir)  # 작업 디렉토리를 출력 디렉토리로 설정
    )
    
    # 디버깅 정보 로깅
    if result.stdout:
        logger.debug(f"LibreOffice stdout: {result.stdout}")
    if result.stderr:
        logger.debug(f"LibreOffice stderr: {result.stderr}")
    
    # stderr에 에러가 있으면 실패로 처리 (returncode가 0이어도)
    has_error = False
    if result.stderr:
        error_lower = result.stderr.lower()
        if any(keyword in error_lower for keyword in ["error", "failed", "fail"]):
            has_error = True
    
    if result.returncode != 0 or has_error:
        error_msg = f"LibreOffice 변환 실패 (returncode: {result.returncode})"
        if result.stderr:
            error_msg += f"\nstderr: {result.stderr}"
        if result.stdout:
            error_msg += f"\nstdout: {result.stdout}"
        
        # 필터 옵션 없이 재시도
        if has_error and "parameter" in error_msg.lower():
            logger.warning("PDF 필터 옵션 오류 감지, 필터 옵션 없이 재시도...")
            return _convert_with_libreoffice_simple(file_path, pdf_path)
        
        raise RuntimeError(error_msg)
    
    # 예상된 PDF 파일명 (입력 파일의 stem 사용)
    input_stem = input_file.stem
    expected_pdf = output_dir / f"{input_stem}.pdf"
    
    # PDF 파일 찾기 (대소문자 구분 없이)
    if expected_pdf.exists():
        logger.info(f"PDF 변환 성공 (LibreOffice, 고품질): {file_path} -> {expected_pdf}")
        return str(expected_pdf)
    
    # 파일이 없으면 출력 디렉토리에서 모든 PDF 파일 검색
    pdf_files = list(output_dir.glob("*.pdf"))
    if pdf_files:
        # 가장 최근에 수정된 PDF 파일 사용
        latest_pdf = max(pdf_files, key=lambda p: p.stat().st_mtime)
        logger.info(f"PDF 파일 발견 (예상과 다름): {latest_pdf}")
        logger.info(f"PDF 변환 성공 (LibreOffice, 고품질): {file_path} -> {latest_pdf}")
        return str(latest_pdf)
    
    # 여전히 파일이 없으면 에러
    error_msg = (
        f"PDF 파일이 생성되지 않았습니다.\n"
        f"예상 경로: {expected_pdf}\n"
        f"입력 파일: {input_file}\n"
        f"출력 디렉토리: {output_dir}\n"
        f"LibreOffice returncode: {result.returncode}\n"
    )
    if result.stdout:
        error_msg += f"stdout: {result.stdout}\n"
    if result.stderr:
        error_msg += f"stderr: {result.stderr}"
    raise RuntimeError(error_msg)


def _convert_with_libreoffice_simple(file_path: str, pdf_path: Path) -> str:
    """
    LibreOffice를 사용한 PDF 변환 (단순 버전, 필터 옵션 없음)
    필터 옵션 오류 시 대체 방법으로 사용
    """
    libreoffice_cmd = _find_libreoffice_command()
    
    input_file = Path(file_path).resolve()
    output_dir = pdf_path.parent.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    
    cmd = [
        libreoffice_cmd,
        "--headless",
        "--nodefault",
        "--nolockcheck",
        "--convert-to", "pdf",
        "--outdir", str(output_dir),
        str(input_file)
    ]
    
    logger.debug(f"LibreOffice 명령어 실행 (단순 버전): {' '.join(cmd)}")
    
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=120,
        cwd=str(output_dir)
    )
    
    if result.stdout:
        logger.debug(f"LibreOffice stdout: {result.stdout}")
    if result.stderr:
        logger.debug(f"LibreOffice stderr: {result.stderr}")
    
    if result.returncode != 0:
        error_msg = f"LibreOffice 변환 실패 (returncode: {result.returncode})"
        if result.stderr:
            error_msg += f"\nstderr: {result.stderr}"
        if result.stdout:
            error_msg += f"\nstdout: {result.stdout}"
        raise RuntimeError(error_msg)
    
    input_stem = input_file.stem
    expected_pdf = output_dir / f"{input_stem}.pdf"
    
    if expected_pdf.exists():
        logger.info(f"PDF 변환 성공 (LibreOffice, 단순 버전): {file_path} -> {expected_pdf}")
        return str(expected_pdf)
    
    pdf_files = list(output_dir.glob("*.pdf"))
    if pdf_files:
        latest_pdf = max(pdf_files, key=lambda p: p.stat().st_mtime)
        logger.info(f"PDF 변환 성공 (LibreOffice, 단순 버전): {file_path} -> {latest_pdf}")
        return str(latest_pdf)
    
    error_msg = (
        f"PDF 파일이 생성되지 않았습니다.\n"
        f"예상 경로: {expected_pdf}\n"
        f"입력 파일: {input_file}\n"
        f"출력 디렉토리: {output_dir}\n"
        f"LibreOffice returncode: {result.returncode}\n"
    )
    if result.stdout:
        error_msg += f"stdout: {result.stdout}\n"
    if result.stderr:
        error_msg += f"stderr: {result.stderr}"
    raise RuntimeError(error_msg)


def _convert_with_docx2pdf(file_path: str, pdf_path: Path) -> str:
    """
    docx2pdf를 사용한 PDF 변환 (Windows, Word만)
    주의: docx2pdf는 내부적으로 Word COM을 사용하므로 이미지 품질은 Word COM과 유사
    """
    try:
        from docx2pdf import convert
        
        # docx2pdf는 출력 경로를 직접 지정
        # 내부적으로 Word COM을 사용하므로 기본적으로 고품질 변환
        convert(str(file_path), str(pdf_path))
        
        if pdf_path.exists():
            logger.info(f"PDF 변환 성공 (docx2pdf, 고품질): {file_path} -> {pdf_path}")
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
    이미지 품질 및 한글 폰트 유지를 위한 최적화 설정 적용
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
                # 이미지 품질 및 한글 폰트 유지를 위한 고품질 PDF 변환
                # OptimizeForPrint=False: 화면 최적화 비활성화 (고품질 유지)
                # CreateBookmarks=2: 모든 제목에 책갈피 생성
                # Word는 기본적으로 사용된 폰트를 임베드하므로 한글 폰트도 자동으로 포함됨
                # 이미지 압축 비활성화를 위해 문서의 이미지 압축 설정 확인 및 조정
                try:
                    # 문서의 모든 이미지에 대해 압축 비활성화 시도
                    for shape in doc.Shapes:
                        if hasattr(shape, 'PictureFormat'):
                            try:
                                # 이미지 압축 비활성화 (가능한 경우)
                                if hasattr(shape.PictureFormat, 'Compress'):
                                    shape.PictureFormat.Compress = 0  # msoFalse = 0
                            except:
                                pass
                except:
                    pass
                
                doc.SaveAs2(
                    pdf_path_resolved,
                    FileFormat=17,  # wdFormatPDF = 17
                    OptimizeForPrint=False,  # 인쇄 최적화 비활성화로 이미지 품질 유지
                    CreateBookmarks=2,  # 모든 제목에 책갈피 생성
                    EmbedTrueTypeFonts=True,  # TrueType 폰트 임베드 (한글 폰트 포함)
                    UseISO19005_1=False  # PDF/A 표준 비활성화 (이미지 품질 유지)
                )
                doc.Close()
                logger.info(f"PDF 변환 성공 (Word COM, 고품질): {file_path} -> {pdf_path}")
                return pdf_path_resolved
            finally:
                app.Quit()
        elif file_ext in [".xlsx", ".xls"]:
            # Excel COM 사용 (DataFrame 변환은 convert_to_pdf에서 이미 시도됨)
            # 여기서는 Excel COM만 사용
            app = win32com.client.Dispatch("Excel.Application")
            app.Visible = False
            try:
                wb = app.Workbooks.Open(file_path_resolved)
                
                # 모든 워크시트의 페이지 설정을 조정하여 표 형식 유지
                xlLandscape = 2
                xlPortrait = 1
                for ws in wb.Worksheets:
                    try:
                        # 숨겨진 행/열 표시 (모든 데이터가 PDF에 포함되도록)
                        try:
                            ws.Columns.Hidden = False
                            ws.Rows.Hidden = False
                        except:
                            pass
                        
                        # 인쇄 영역을 사용된 범위 전체로 설정 (모든 데이터 포함)
                        try:
                            used_range = ws.UsedRange
                            if used_range:
                                ws.PageSetup.PrintArea = used_range.Address
                        except:
                            pass
                        
                        # 페이지 설정 조정
                        page_setup = ws.PageSetup
                        
                        # 표 형식 유지를 위한 설정
                        # 각 행이 한 페이지를 차지하도록 설정
                        # FitToPagesWide=1: 한 페이지 너비에 맞춤 (표가 잘리지 않도록)
                        # FitToPagesTall=1: 각 행이 한 페이지 높이에 맞춤
                        page_setup.FitToPagesWide = 1
                        page_setup.FitToPagesTall = 1  # 각 행이 한 페이지를 차지하도록
                        
                        # 격자선 인쇄 (표 형식 유지) - 표를 더 이쁘게 보이게 함
                        page_setup.PrintGridlines = True
                        
                        # 행/열 제목 인쇄 안 함
                        page_setup.PrintHeadings = False
                        
                        # 여백 최소화 (표가 더 넓게 표시되도록)
                        page_setup.LeftMargin = app.InchesToPoints(0.25)
                        page_setup.RightMargin = app.InchesToPoints(0.25)
                        page_setup.TopMargin = app.InchesToPoints(0.25)
                        page_setup.BottomMargin = app.InchesToPoints(0.25)
                        
                        # 페이지 방향은 가로로 설정 (표가 넓을 경우)
                        page_setup.Orientation = xlLandscape
                        
                        # 사용된 범위 가져오기
                        try:
                            used_range = ws.UsedRange
                            if used_range:
                                # 모든 셀에 테두리 추가 (표 형식을 명확하게)
                                xlContinuous = 1
                                xlThin = 2
                                xlMedium = 4
                                
                                # 전체 범위에 테두리 적용
                                used_range.Borders.LineStyle = xlContinuous
                                used_range.Borders.Weight = xlThin
                                
                                # 외곽 테두리를 더 굵게
                                used_range.BorderAround(LineStyle=xlContinuous, Weight=xlMedium)
                                
                                # 셀 정렬 설정
                                # 왼쪽 정렬 (텍스트 가독성 향상)
                                used_range.HorizontalAlignment = -4131  # xlLeft
                                used_range.VerticalAlignment = -4107  # xlCenter
                                
                                # 텍스트 줄바꿈 활성화 (긴 텍스트 표시)
                                used_range.WrapText = True
                                
                                # 폰트 크기 조정 (가독성 향상, 글자 겹침 방지)
                                used_range.Font.Size = 7
                                
                                # 셀 여백 설정 (글자 겹침 방지)
                                try:
                                    used_range.IndentLevel = 0
                                    # 셀 내부 여백 설정
                                    used_range.LeftIndent = 0
                                    used_range.RightIndent = 0
                                except:
                                    pass
                                
                                # 첫 번째 행을 헤더로 강조
                                if used_range.Rows.Count > 0:
                                    first_row = used_range.Rows(1)
                                    first_row.Font.Bold = True
                                    first_row.Font.Size = 9
                                    first_row.Interior.Color = 0xD0D0D0  # 회색 배경
                                    first_row.HorizontalAlignment = -4108  # xlCenter
                                    first_row.VerticalAlignment = -4107  # xlCenter
                                    
                                    # 첫 번째 행 테두리를 더 굵게
                                    first_row.Borders.Weight = xlMedium
                                    
                                    # 첫 번째 행 하단 테두리를 더 굵게 (헤더 구분)
                                    first_row.Borders(10).Weight = xlMedium  # xlEdgeBottom
                                
                                # 열 너비 자동 조정 (내용에 맞게, 충분한 여유 공간 확보)
                                try:
                                    for col in range(1, used_range.Columns.Count + 1):
                                        col_obj = ws.Columns(col)
                                        # 먼저 자동 맞춤
                                        col_obj.AutoFit()
                                        
                                        # 최소 너비를 충분히 설정 (글자 겹침 방지)
                                        current_width = col_obj.ColumnWidth
                                        if current_width < 20:
                                            col_obj.ColumnWidth = 20  # 최소 너비 증가
                                        # 최대 너비 제한 (너무 넓어지지 않도록)
                                        elif current_width > 70:
                                            col_obj.ColumnWidth = 70
                                        else:
                                            # 여유 공간 추가 (20% 여유, 더 넓게)
                                            col_obj.ColumnWidth = current_width * 1.2
                                except Exception as e:
                                    logger.warning(f"열 너비 조정 실패: {e}")
                                
                                # 각 행이 한 페이지를 차지하도록 행 높이 및 페이지 나누기 설정
                                try:
                                    # 페이지 높이 계산 (인치 단위)
                                    # A4 가로 방향: 11.69인치 (높이)
                                    # 여백 제외: 11.69 - 0.25 - 0.25 = 11.19인치
                                    # 포인트로 변환: 11.19 * 72 = 약 805 포인트
                                    page_height_points = (11.69 - 0.25 - 0.25) * 72  # 약 805 포인트
                                    
                                    xlPageBreakManual = -4135
                                    
                                    # 헤더 행은 작게 유지
                                    if used_range.Rows.Count > 0:
                                        first_row = used_range.Rows(1)
                                        first_row.AutoFit()
                                        header_height = first_row.RowHeight
                                        if header_height > 30:
                                            first_row.RowHeight = 30
                                            header_height = 30
                                    
                                    # 각 데이터 행마다 페이지 나누기 추가 및 높이 설정
                                    page_break_count = 0
                                    for row in range(2, used_range.Rows.Count + 1):
                                        row_obj = used_range.Rows(row)
                                        
                                        # 자동 맞춤으로 최소 높이 계산
                                        row_obj.AutoFit()
                                        current_height = row_obj.RowHeight
                                        
                                        # 각 행의 높이를 페이지 높이에 맞춤
                                        # 페이지 높이의 85% 정도로 설정 (여백 확보)
                                        target_height = page_height_points * 0.85
                                        if current_height < target_height:
                                            row_obj.RowHeight = target_height
                                            final_height = target_height
                                        else:
                                            final_height = current_height
                                        
                                        # 각 행 앞에 페이지 나누기 추가
                                        page_break_added = False
                                        try:
                                            ws.Rows(row).PageBreak = xlPageBreakManual
                                            page_break_added = True
                                            page_break_count += 1
                                        except:
                                            # 대체 방법: HPageBreaks 사용
                                            try:
                                                ws.HPageBreaks.Add(ws.Rows(row))
                                                page_break_added = True
                                                page_break_count += 1
                                            except:
                                                pass
                                        
                                    logger.debug(f"워크시트 '{ws.Name}' 각 행을 한 페이지로 설정 완료 (총 {used_range.Rows.Count}행)")
                                except Exception as e:
                                    logger.warning(f"행 높이 조정 실패: {e}")
                                
                                logger.debug(f"워크시트 '{ws.Name}' 셀 스타일 적용 완료 (테두리, 정렬, 헤더, 자동 맞춤, 여유 공간 확보)")
                        except Exception as e:
                            logger.warning(f"워크시트 '{ws.Name}' 셀 스타일 적용 실패: {e}")
                        
                        logger.debug(f"워크시트 '{ws.Name}' 페이지 설정 완료 (표 형식 유지 및 스타일 적용)")
                    except Exception as e:
                        logger.warning(f"워크시트 '{ws.Name}' 페이지 설정 실패: {e}")
                
                # 이미지 품질 및 한글 폰트 유지를 위한 고품질 PDF 변환
                # Quality=0: xlQualityStandard (표준 품질, 이미지 유지)
                # Excel은 기본적으로 사용된 폰트를 임베드하므로 한글 폰트도 자동으로 포함됨
                # IncludeDocProperties=True: 문서 속성 포함
                # IgnorePrintAreas=False: 인쇄 영역 무시하지 않음 (전체 내용 포함)
                # 모든 워크시트를 PDF에 포함
                wb.ExportAsFixedFormat(
                    Type=0,  # xlTypePDF = 0
                    Filename=pdf_path_resolved,
                    Quality=0,  # xlQualityStandard = 0 (표준 품질, 이미지 유지)
                    IncludeDocProperties=True,
                    IgnorePrintAreas=False,  # 인쇄 영역 무시하지 않음 (전체 내용 포함)
                    OpenAfterPublish=False,
                    From=1,  # 첫 번째 페이지
                    To=0,  # 마지막 페이지까지 (0이면 모든 페이지)
                    OptimizeForPrint=False  # 인쇄 최적화 비활성화 (모든 내용 포함)
                )
                
                # PDF 파일 확인
                if not Path(pdf_path_resolved).exists():
                    logger.warning("PDF 파일이 생성되지 않았습니다!")
                
                wb.Close(False)
                logger.info(f"PDF 변환 성공 (Excel COM, 고품질, 표 형식 유지): {file_path} -> {pdf_path}")
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
                # PowerPoint의 SaveAs는 기본적으로 고품질로 변환되며
                # 이미지 품질과 폰트(한글 포함)가 유지됩니다
                # PowerPoint는 기본적으로 사용된 폰트를 임베드합니다
                presentation.SaveAs(
                    pdf_path_resolved,
                    FileFormat=32  # ppSaveAsPDF = 32
                )
                presentation.Close()
                logger.info(f"PDF 변환 성공 (PowerPoint COM, 고품질): {file_path} -> {pdf_path}")
                return pdf_path_resolved
            finally:
                app.Quit()
        else:
            raise RuntimeError(f"지원하지 않는 파일 형식: {file_ext}")
            
    except ImportError:
        raise RuntimeError("pywin32가 설치되어 있지 않습니다. pip install pywin32")
    except Exception as e:
        raise RuntimeError(f"Office COM 변환 실패: {str(e)}")


def convert_to_pdf(file_path: str, output_dir: Optional[str] = None, original_file_path: Optional[str] = None) -> str:
    """
    Word/Excel/PPT/HTML 파일을 PDF로 변환
    이미지 품질과 한글 폰트를 유지하면서 고품질 PDF로 변환합니다.
    
    플랫폼별로 다른 방법 사용:
    - Windows: LibreOffice (우선, 모든 형식) > Office COM (Word/Excel/PPT만) > docx2pdf (Word만)
    - Linux/Mac: LibreOffice (모든 형식)
    
    모든 플랫폼에서 LibreOffice를 우선 사용하여 일관된 품질과 한글 폰트 보호를 제공합니다.
    
    모든 변환 방법에서 다음 최적화 설정이 적용됩니다:
    - 이미지 품질 유지 (고해상도 유지)
    - 한글 폰트 임베드 (폰트 깨짐 방지)
    - 모든 사용된 폰트 임베드
    
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
    
    # HTML 파일인 경우 이미지 경로 처리
    processed_html_path = None
    if file_ext in [".html", ".htm"]:
        try:
            processed_html_path = _prepare_html_for_conversion(file_path)
            file_path = processed_html_path  # 처리된 HTML 파일 사용
        except Exception as e:
            logger.warning(f"HTML 이미지 경로 처리 실패, 원본 사용: {e}")
    
    # 출력 디렉토리 설정
    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        pdf_path = output_path / f"{file_path_obj.stem}.pdf"
    else:
        temp_dir = Path(tempfile.gettempdir())
        pdf_path = temp_dir / f"{file_path_obj.stem}_{file_ext[1:]}.pdf"
    
    # HTML 파일인 경우 Playwright 우선 시도 (이미지 렌더링이 더 정확함)
    if file_ext in [".html", ".htm"]:
        try:
            result = _convert_with_playwright(file_path, pdf_path)
            # 처리된 임시 HTML 파일 정리
            if processed_html_path and processed_html_path != file_path:
                try:
                    Path(processed_html_path).unlink()
                except:
                    pass
            return result
        except Exception as e:
            logger.warning(f"Playwright 변환 실패, LibreOffice 시도: {e}")
    
    # Excel 파일인 경우 DataFrame 변환을 우선 시도 (모든 플랫폼)
    if file_ext in [".xlsx", ".xls"]:
        try:
            import pandas as pd
            logger.info("Excel 파일을 DataFrame 방식으로 변환 시도 (우선)")
            return _convert_excel_with_dataframe(file_path, pdf_path, original_file_path=original_file_path)
        except ImportError as e:
            logger.debug(f"pandas가 설치되어 있지 않아 DataFrame 변환을 건너뜁니다: {e}")
        except Exception as e:
            logger.warning(f"DataFrame 변환 실패, 다른 방법 시도: {e}", exc_info=True)
    
    # Windows인 경우
    if sys.platform == "win32":
        # 방법 1: LibreOffice 우선 시도 (모든 형식, 일관된 품질)
        # LibreOffice는 모든 플랫폼에서 동일한 품질과 한글 폰트 보호를 제공
        try:
            return _convert_with_libreoffice(file_path, pdf_path)
        except FileNotFoundError:
            logger.warning("LibreOffice를 찾을 수 없습니다. 다른 방법 시도...")
        except Exception as e:
            logger.warning(f"LibreOffice 변환 실패, 다른 방법 시도: {e}")
        
        # 방법 2: Office COM 객체 시도 (Word/Excel/PPT만, 대체 방법)
        if file_ext in [".docx", ".xlsx", ".xls", ".pptx", ".ppt"]:
            try:
                return _convert_with_office_com(file_path, pdf_path)
            except Exception as e:
                logger.warning(f"Office COM 변환 실패, 다른 방법 시도: {e}")
        
        # 방법 3: docx2pdf 시도 (Word만, 대체 방법)
        if file_ext == ".docx":
            try:
                return _convert_with_docx2pdf(file_path, pdf_path)
            except Exception as e:
                logger.warning(f"docx2pdf 변환 실패: {e}")
        
        # 모든 방법 실패
        error_msg = (
            "PDF 변환 도구를 찾을 수 없습니다.\n"
            "다음 중 하나를 설치하세요:\n"
            "1. LibreOffice (권장, https://www.libreoffice.org/download/)\n"
            "2. Microsoft Office (Word/Excel)\n"
            "3. docx2pdf (pip install docx2pdf) - Word만"
        )
        raise RuntimeError(error_msg)
    
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


def upload_pdf_to_minio(
    pdf_path: str,
    object_name: Optional[str] = None,
    bucket_name: Optional[str] = None
) -> str:
    """
    PDF 파일을 MinIO에 업로드
    
    Args:
        pdf_path: 업로드할 PDF 파일 경로
        object_name: MinIO 객체 이름 (None이면 파일명 사용)
        bucket_name: 버킷 이름 (None이면 기본 버킷 사용)
    
    Returns:
        업로드된 객체의 전체 URL (https://storage.ragextension.shop/bucket/object_name)
    
    Raises:
        RuntimeError: 업로드 실패 시
    """
    try:
        from minio import Minio
        from minio.error import S3Error
    except ImportError:
        raise RuntimeError("minio 라이브러리가 설치되어 있지 않습니다. pip install minio")
    
    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        raise FileNotFoundError(f"PDF 파일을 찾을 수 없습니다: {pdf_path}")
    
    # MinIO 클라이언트 초기화
    client = Minio(
        endpoint=settings.minio_endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        secure=settings.minio_secure
    )
    
    # 버킷 이름 설정
    bucket = bucket_name or settings.minio_bucket_name
    
    # 객체 이름 설정
    if object_name is None:
        # 타임스탬프를 포함한 고유한 파일명 생성
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        object_name = f"{pdf_file.stem}_{timestamp}.pdf"
    
    # 버킷이 존재하는지 확인하고 없으면 생성
    try:
        bucket_exists = client.bucket_exists(bucket)
        if not bucket_exists:
            client.make_bucket(bucket)
            logger.info(f"MinIO 버킷 생성: {bucket}")
        
        # 버킷 공개 읽기 정책 설정 (파일 공개 접근 허용)
        try:
            import json
            policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"AWS": ["*"]},
                        "Action": ["s3:GetObject"],
                        "Resource": [f"arn:aws:s3:::{bucket}/*"]
                    }
                ]
            }
            policy_json = json.dumps(policy)
            client.set_bucket_policy(bucket, policy_json)
            logger.info(f"MinIO 버킷 공개 읽기 정책 설정 완료: {bucket}")
        except S3Error as e:
            logger.warning(f"버킷 정책 설정 중 오류 (계속 진행): {e}")
    except S3Error as e:
        logger.warning(f"버킷 확인/생성 중 오류 (계속 진행): {e}")
    
    # PDF 파일 읽기
    try:
        with open(pdf_path, 'rb') as file_data:
            file_size = pdf_file.stat().st_size
            
            # MinIO에 업로드
            client.put_object(
                bucket_name=bucket,
                object_name=object_name,
                data=file_data,
                length=file_size,
                content_type='application/pdf'
            )
            
            # 전체 URL 생성
            base_url = settings.minio_base_url.rstrip('/')
            full_url = f"{base_url}/{bucket}/{object_name}"
            
            logger.info(f"PDF 파일 MinIO 업로드 완료: {full_url} ({file_size} bytes)")
            return full_url
            
    except S3Error as e:
        logger.error(f"MinIO 업로드 실패: {e}")
        raise RuntimeError(f"MinIO 업로드 실패: {str(e)}")
    except Exception as e:
        logger.error(f"PDF 파일 읽기/업로드 실패: {e}")
        raise RuntimeError(f"PDF 파일 업로드 중 오류 발생: {str(e)}")


def convert_to_pdf_and_upload(
    file_path: str,
    output_dir: Optional[str] = None,
    object_name: Optional[str] = None,
    bucket_name: Optional[str] = None,
    upload_to_minio: bool = True,
    original_file_path: Optional[str] = None
) -> tuple[str, Optional[str]]:
    """
    파일을 PDF로 변환하고 MinIO에 업로드
    
    Args:
        file_path: 변환할 파일 경로
        output_dir: 출력 디렉토리 (None이면 임시 디렉토리 사용)
        object_name: MinIO 객체 이름 (None이면 자동 생성)
        bucket_name: MinIO 버킷 이름 (None이면 기본 버킷 사용)
        upload_to_minio: MinIO에 업로드할지 여부 (기본값: True)
        original_file_path: 원본 파일 경로 (이미지 추출용, 전치된 파일인 경우 제공)
    
    Returns:
        (pdf_path, minio_path) 튜플
        - pdf_path: 생성된 PDF 파일 경로
        - minio_path: MinIO 업로드 경로 (bucket/object_name), 업로드하지 않은 경우 None
    
    Raises:
        RuntimeError: 변환 또는 업로드 실패 시
    """
    # PDF 변환
    pdf_path = convert_to_pdf(file_path, output_dir, original_file_path=original_file_path)
    
    # MinIO 업로드
    minio_path = None
    if upload_to_minio:
        try:
            minio_path = upload_pdf_to_minio(pdf_path, object_name, bucket_name)
        except Exception as e:
            logger.warning(f"MinIO 업로드 실패 (PDF 파일은 생성됨): {e}")
            # 업로드 실패해도 PDF 파일은 반환
    
    return pdf_path, minio_path
