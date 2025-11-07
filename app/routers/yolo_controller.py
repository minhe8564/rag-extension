"""
YOLO API 라우터
문서 레이아웃 객체 감지 엔드포인트 제공
"""
import json
import time
from typing import List, Optional
import numpy as np
import cv2
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status

from app.core.settings import settings
from app.core.schemas.response import BaseResponse, Result
from app.processors.yolo_processor import YOLOProcessor

router = APIRouter(
    prefix="/yolo",
    tags=["YOLO"]
)

# YOLO 프로세서 인스턴스 (싱글톤)
_yolo_processor = None

def get_yolo_processor() -> YOLOProcessor:
    """YOLO 프로세서 인스턴스 가져오기 (싱글톤)"""
    global _yolo_processor
    if _yolo_processor is None:
        _yolo_processor = YOLOProcessor()
    return _yolo_processor

@router.get("/health")
async def yolo_health():
    """YOLO 서비스 헬스체크"""
    processor = get_yolo_processor()
    return {
        "status": "healthy",
        "device": processor._device,
        "weights": settings.YOLO_WEIGHTS,
        "conf": settings.YOLO_CONF
    }

@router.post("/detect-bboxes", response_model=BaseResponse[dict])
async def detect_bboxes(
    images: List[UploadFile] = File(..., description="페이지 이미지들 (PNG/JPEG)"),
    pages_json: str = Form(..., description="[1,2,3] 형태의 페이지 번호 배열(JSON)"),
    conf: Optional[float] = Form(None, description="confidence 임계값(미지정 시 설정값 사용)")
):
    """
    바운딩 박스 감지
    - 다중 이미지 업로드 지원
    - 메모리에서 직접 처리 (디스크 저장 없음)
    """
    t0 = time.perf_counter()
    
    try:
        # 페이지 번호 파싱
        pages = list(map(int, json.loads(pages_json)))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"pages_json must be a JSON array of page numbers: {e}"
        )
    
    if len(images) != len(pages):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"images count ({len(images)}) must match pages length ({len(pages)})"
        )
    
    # 메모리에서 이미지 디코딩 (디스크 저장 없음)
    pairs = []
    for img, pno in zip(images, pages):
        try:
            buf = np.frombuffer(await img.read(), dtype=np.uint8)
            bgr = cv2.imdecode(buf, cv2.IMREAD_COLOR)
            if bgr is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"failed to decode image for page {pno}"
                )
            pairs.append((pno, bgr))
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"failed to process image for page {pno}: {e}"
            )
    
    # YOLO 추론 (가중치는 settings에서 자동으로 사용됨)
    try:
        processor = get_yolo_processor()
        detections = processor.detect_bboxes(pairs, weights=None, conf=conf)
        
        timing_sec = round(time.perf_counter() - t0, 3)
        
        return BaseResponse(
            status=200,
            code="SUCCESS",
            message="바운딩 박스 감지 성공",
            isSuccess=True,
            result=Result(data={
                "detections": detections,
                "timing_sec": timing_sec,
            })
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"YOLO 추론 실패: {str(e)}"
        )