"""
PDF 파일 프로세서
PDF 파일을 Markdown으로 변환
"""

import logging
import threading
import torch
from pathlib import Path
from typing import Dict, Any, List

from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.output import text_from_rendered

from app.core.settings import settings
from app.core.utils.pdf_converter import upload_pdf_to_minio
from .base import BaseProcessor

logger = logging.getLogger(__name__)

class PDFProcessor(BaseProcessor):
    """
    PDF 파일을 Markdown으로 변환하는 프로세서
    """

    @property
    def supported_extensions(self) -> List[str]:
        """
        지원하는 파일 확장자
        """
        return [".pdf"]

    def __init__(self):
        self._model_dict = None
        self._lock = threading.Lock()
        
        # settings에서 명시적으로 device가 지정된 경우
        requested_device = settings.marker_device.lower()
        if requested_device in ["cuda", "mps", "cpu"]:
            # 명시적으로 지정된 device 사용 (사용 가능한지 확인)
            if requested_device == "cuda" and torch.cuda.is_available():
                self._device = "cuda"
            elif requested_device == "mps" and torch.backends.mps.is_available():
                self._device = "mps"
            elif requested_device == "cpu":
                self._device = "cpu"
            else:
                # 지정된 device를 사용할 수 없으면 자동 선택
                logger.warning(f"{requested_device}를 사용하도록 설정되어 있지만 사용할 수 없습니다. 자동으로 다른 device로 전환합니다.")
                self._device = self._auto_select_device()
        else:
            # 자동으로 device 선택 (우선순위: CUDA > MPS > CPU)
            self._device = self._auto_select_device()
        
        # dtype 설정
        if self._device == "cpu":
            self._dtype = "float32"
            self._dtype_t = torch.float32
        else:
            # CUDA/MPS는 설정값 사용, 없으면 float16
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
        lifespan 이벤트에서 미리 로드되거나, 첫 요청 시 lazy loading으로 로드됨
        """
        # 빠른 경로: 이미 로드되어 있으면 바로 반환
        if self._model_dict is not None:
            return self._model_dict

        with self._lock:
            # 더블체크: 다른 스레드가 이미 로드했을 수 있음
            if self._model_dict is not None:
                return self._model_dict

            try:
                print(f"[Marker 모델] 로딩 시작 - Device: {self._device.upper()}, Dtype: {self._dtype}")
                logger.info(f"[Marker 모델] 로딩 시작 - Device: {self._device.upper()}, Dtype: {self._dtype}")
                kwargs = {"device": self._device}
                if self._dtype_t is not None:
                    kwargs["dtype"] = self._dtype_t
                self._model_dict = create_model_dict(**kwargs)
                print(f"[Marker 모델] 로드 완료 - Device: {self._device.upper()}, Dtype: {self._dtype}")
                logger.info(f"[Marker 모델] 로드 완료 - Device: {self._device.upper()}, Dtype: {self._dtype}")
            except TypeError:
                print(f"[Marker 모델] 로딩 시작 (dtype 제외) - Device: {self._device.upper()}")
                logger.info(f"[Marker 모델] 로딩 시작 (dtype 제외) - Device: {self._device.upper()}")
                self._model_dict = create_model_dict(device=self._device)
                print(f"[Marker 모델] 로드 완료 - Device: {self._device.upper()}")
                logger.info(f"[Marker 모델] 로드 완료 - Device: {self._device.upper()}")

            return self._model_dict
    
    def process(self, file_path: str) -> Dict[str, Any]:
        """
        PDF -> MinIO 업로드 -> Markdown 변환
        """
        if not Path(file_path).exists():
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")

        minio_path = None
        try:
            # 1. PDF 파일을 MinIO에 업로드
            logger.info(f"PDF 파일을 MinIO에 업로드 시작: {file_path}")
            minio_path = upload_pdf_to_minio(file_path)
            logger.info(f"MinIO 업로드 완료: {minio_path}")
            
            # 2. 모델 로드
            mdict = self._ensure_model()

            # 3. PDF 변환
            conv = PdfConverter(artifact_dict=mdict)
            rendered = conv(file_path)
            md_text, _, images = text_from_rendered(rendered)
            
            return {
                "content": md_text,
                "metadata": {
                    "file_type": "pdf",
                    "device": self._device,
                    "dtype": self._dtype,
                    "image_count": len(images) if images else 0,
                    "minio_path": minio_path,  # MinIO 업로드 경로 추가
                }
            }
        except Exception as e:
            logger.error(f"PDF 처리 실패: {file_path}, 오류: {e}", exc_info=True)
            raise