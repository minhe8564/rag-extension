"""
YOLO 프로세서
문서 레이아웃 객체(figure/table) 바운딩 박스 감지
"""
import logging
import threading
import torch
from pathlib import Path
from typing import List, Tuple, Dict, Any

import numpy as np
from doclayout_yolo import YOLOv10

from app.core.settings import settings

logger = logging.getLogger(__name__)

class YOLOProcessor:
    """
    YOLO를 사용한 문서 레이아웃 객체 감지 프로세서
    """
    
    def __init__(self):
        self._model = None
        self._weights_loaded_from = None
        self._lock = threading.Lock()
        
        # 디바이스 자동 선택 (CUDA > MPS > CPU)
        requested_device = settings.YOLO_DEVICE.lower()
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
            # 자동으로 device 선택 (우선순위: CUDA > MPS > CPU)
            self._device = self._auto_select_device()
        
        mps_available = torch.backends.mps.is_available() if hasattr(torch.backends, 'mps') else False
        cuda_available = torch.cuda.is_available()
        
        # print로도 출력 (로깅 설정 전에도 보이도록)
        print("=" * 80)
        print(f"[YOLOProcessor] Device 선택 완료")
        print(f"  - 선택된 Device: {self._device.upper()}")
        print(f"  - CUDA 사용 가능: {cuda_available}")
        print(f"  - MPS 사용 가능: {mps_available}")
        print(f"  - 설정값 (YOLO_DEVICE): {settings.YOLO_DEVICE}")
        print(f"  - 설정값 (YOLO_WEIGHTS): {settings.YOLO_WEIGHTS}")
        print(f"  - 설정값 (YOLO_CONF): {settings.YOLO_CONF}")
        print("=" * 80)
        
        logger.info("=" * 80)
        logger.info(f"[YOLOProcessor] Device 선택 완료")
        logger.info(f"  - 선택된 Device: {self._device.upper()}")
        logger.info(f"  - CUDA 사용 가능: {cuda_available}")
        logger.info(f"  - MPS 사용 가능: {mps_available}")
        logger.info(f"  - 설정값 (YOLO_DEVICE): {settings.YOLO_DEVICE}")
        logger.info(f"  - 설정값 (YOLO_WEIGHTS): {settings.YOLO_WEIGHTS}")
        logger.info(f"  - 설정값 (YOLO_CONF): {settings.YOLO_CONF}")
        logger.info("=" * 80)
    
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
    
    def _ensure_model(self, weights: str) -> YOLOv10:
        """
        YOLO 모델을 싱글톤으로 로드 (thread-safe)
        """
        # 빠른 경로: 이미 로드되어 있고 같은 가중치 파일이면 바로 반환
        if self._model is not None and self._weights_loaded_from == weights:
            return self._model
        
        with self._lock:
            # 더블체크: 다른 스레드가 이미 로드했을 수 있음
            if self._model is not None and self._weights_loaded_from == weights:
                return self._model
            
            try:
                print(f"[YOLO 모델] 로딩 시작 - Device: {self._device.upper()}, Weights: {weights}")
                logger.info(f"[YOLO 모델] 로딩 시작 - Device: {self._device.upper()}, Weights: {weights}")
                
                model = YOLOv10(str(weights))
                
                # 디바이스로 이동
                try:
                    if hasattr(model, "to"):
                        model.to(self._device)
                    elif hasattr(model, "model") and hasattr(model.model, "to"):
                        model.model.to(self._device)
                except Exception as e:
                    logger.warning(f"모델을 {self._device}로 이동하는데 실패했습니다: {e}")
                
                self._model = model
                self._weights_loaded_from = weights
                
                print(f"[YOLO 모델] 로드 완료 - Device: {self._device.upper()}")
                logger.info(f"[YOLO 모델] 로드 완료 - Device: {self._device.upper()}")
                
            except Exception as e:
                logger.error(f"YOLO 모델 로딩 실패: {e}", exc_info=True)
                raise
        
        return self._model
    
    def _device_arg_for_predict(self) -> str | int:
        """
        predict 메서드에 전달할 device 인자 변환
        """
        if self._device.startswith("cuda"):
            parts = self._device.split(":")
            return int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
        elif self._device == "mps":
            return "mps"
        else:
            return "cpu"
    
    def detect_bboxes(
        self,
        pages_bgr: List[Tuple[int, np.ndarray]],
        weights: str | None = None,
        conf: float | None = None
    ) -> List[Dict[str, Any]]:
        """
        바운딩 박스 감지
        """
        # 가중치 및 confidence 설정
        w = weights or settings.YOLO_WEIGHTS
        c = conf if conf is not None else settings.YOLO_CONF
        
        if not Path(w).exists():
            raise FileNotFoundError(f"모델 가중치 파일을 찾을 수 없습니다: {w}")
        
        # 모델 로드
        model = self._ensure_model(w)
        names = getattr(model, "names", {0: "figure", 1: "table"})
        device_arg = self._device_arg_for_predict()
        
        out = []
        for pno, im in pages_bgr:
            try:
                res = model.predict(im, conf=c, device=device_arg)
            except Exception as e:
                logger.warning(f"YOLO 예측 실패 p{pno}: {e}")
                out.append({"page": pno, "items": []})
                continue
            
            r0 = res[0] if isinstance(res, (list, tuple)) else res
            items = []
            
            if hasattr(r0, "boxes") and r0.boxes is not None:
                H, W = im.shape[:2]
                for i, box in enumerate(r0.boxes, start=1):
                    try:
                        # 클래스 추출
                        cls_val = getattr(box, "cls", None)
                        cls_idx = int(cls_val[0] if hasattr(cls_val, "__len__") else cls_val)
                    except Exception:
                        cls_idx = 0
                    
                    label = str(names.get(cls_idx, "unknown")).lower()
                    if label not in {"figure", "table"}:
                        continue
                    
                    # 바운딩 박스 좌표 추출
                    xy = getattr(box, "xyxy", None)
                    if xy is None:
                        continue
                    
                    coords = xy[0] if hasattr(xy, "__len__") else xy
                    try:
                        x1, y1, x2, y2 = map(int, coords)
                    except Exception:
                        continue
                    
                    # 이미지 경계 내로 보정
                    x1 = max(0, min(x1, W - 1))
                    x2 = max(0, min(x2, W))
                    y1 = max(0, min(y1, H - 1))
                    y2 = max(0, min(y2, H))
                    
                    # confidence 추출
                    conf_v = getattr(box, "conf", 0.0)
                    try:
                        conf_v = float(conf_v[0] if hasattr(conf_v, "__len__") else conf_v)
                    except Exception:
                        conf_v = 0.0
                    
                    items.append({
                        "idx": i,
                        "cls": label,
                        "conf": conf_v,
                        "bbox": [x1, y1, x2, y2]
                    })
            
            out.append({"page": pno, "items": items})
        
        return out