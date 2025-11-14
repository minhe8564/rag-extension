"""
HTML 프로세서
HTML 파일(.html, .htm)을 PDF로 변환 후 Marker로 처리
"""
import logging
import threading
import torch
import tempfile
from pathlib import Path
from typing import Dict, Any, List

from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.output import text_from_rendered

from app.core.settings import settings
from app.core.utils.pdf_converter import convert_to_pdf
from .base import BaseProcessor

logger = logging.getLogger(__name__)

class HTMLProcessor(BaseProcessor):
    """
    HTML 파일(.html, .htm)을 Markdown으로 변환하는 프로세서
    PDF로 변환 후 Marker로 처리
    """
    @property
    def supported_extensions(self) -> List[str]:
        """
        지원하는 파일 확장자
        """
        return [".html", ".htm"]

    def __init__(self):
        self._model_dict = None  # 언더스코어 추가
        self._lock = threading.Lock()  # 언더스코어 추가
        
        # settings에서 명시적으로 device가 지정된 경우
        requested_device = settings.marker_device.lower()
        if requested_device in ["cuda", "mps", "cpu"]:
            if requested_device == "cuda" and torch.cuda.is_available():
                self._device = "cuda"
            elif requested_device == "mps" and torch.backends.mps.is_available():
                self._device = "mps"
            elif requested_device == "cpu":
                self._device = "cpu"
            else:
                logger.warning(f"{requested_device}를 사용하도록 설정되어 있지만 사용할 수 없습니다. 자동으로 다른 device로 전환합니다.")
                self._device = self._auto_select_device()
        else:
            self._device = self._auto_select_device()
        
        # dtype 설정
        if self._device == "cpu":
            self._dtype = "float32"
            self._dtype_t = torch.float32
        else:
            self._dtype = settings.marker_dtype.lower() if settings.marker_dtype else "float16"
            self._dtype_t = getattr(torch, self._dtype, torch.float16)
    def _auto_select_device(self) -> str:
        """
        자동으로 device 선택 (우선순위: CUDA > MPS > CPU)
        """
        if torch.cuda.is_available():
            return "cuda"
        elif torch.backends.mps.is_available():
            return "mps"
        else:
            return "cpu"
    def _ensure_model(self):
        """
        Marker 모델을 싱글톤으로 로드 (thread-safe)
        PDFProcessor와 동일한 모델 공유
        """
        if self._model_dict is not None:
            return self._model_dict
        
        with self._lock:
            if self._model_dict is not None:
                return self._model_dict
            
            try:
                logger.info(f"[HTML Marker 모델] 로딩 시작 - Device: {self._device.upper()}, Dtype: {self._dtype}")
                kwargs = {"device": self._device}
                if self._dtype_t is not None:
                    kwargs["dtype"] = self._dtype_t
                self._model_dict = create_model_dict(**kwargs)
                logger.info(f"[HTML Marker 모델] 로드 완료 - Device: {self._device.upper()}, Dtype: {self._dtype}")
            except TypeError:
                logger.info(f"[HTML Marker 모델] 로딩 시작 (dtype 제외) - Device: {self._device.upper()}")
                self._model_dict = create_model_dict(device=self._device)
                logger.info(f"[HTML Marker 모델] 로드 완료 - Device: {self._device.upper()}")
            
            return self._model_dict
    def process(self, file_path: str) -> Dict[str, Any]:
        """
        HTML 파일 -> PDF 변환 -> Marker로 Markdown 변환
        """
        if not Path(file_path).exists():
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")
        
        pdf_path = None
        try:
            # 1. HTML 파일을 PDF로 변환 (LibreOffice 사용)
            logger.info(f"HTML 파일을 PDF로 변환 시작: {file_path}")
            pdf_path = convert_to_pdf(file_path)
            logger.info(f"PDF 변환 완료: {pdf_path}")
            
            # 2. PDF를 Marker로 처리
            mdict = self._ensure_model()
            conv = PdfConverter(artifact_dict=mdict)
            rendered = conv(pdf_path)
            md_text, _, images = text_from_rendered(rendered)
            
            logger.info(f"HTML 파일 처리 완료: {file_path}")
            
            return {
                "content": md_text,
                "metadata": {
                    "file_type": Path(file_path).suffix.lower(),
                    "device": self._device,
                    "dtype": self._dtype,
                    "image_count": len(images) if images else 0,
                }
            }
        except Exception as e:
            logger.error(f"HTML 처리 실패: {file_path}, 오류: {e}", exc_info=True)
            raise
        finally:
            # 임시 PDF 파일 정리
            if pdf_path and Path(pdf_path).exists():
                try:
                    # 임시 디렉토리에 있는 파일만 삭제
                    if tempfile.gettempdir() in str(pdf_path):
                        Path(pdf_path).unlink()
                        logger.debug(f"임시 PDF 파일 삭제: {pdf_path}")
                except Exception as e:
                    logger.warning(f"임시 PDF 파일 삭제 실패: {pdf_path}, 오류: {e}")