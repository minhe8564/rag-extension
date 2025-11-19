"""
Marker API 라우터
다양한 파일을 받아 Markdown으로 변환하는 엔드포인트를 제공
"""
import time
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from pathlib import Path

from app.core.settings import settings
from app.core.schemas import BaseResponse, Result
from app.processors import ProcessorFactory
from app.services.file_service import FileService

router = APIRouter(
    prefix="/marker",
    tags=["Marker"]
)

@router.get("/health")
async def marker_health():
    """Marker 서비스 헬스체크"""
    return {
        "status": "healthy",
        "device": settings.marker_device,
        "dtype": settings.marker_dtype
    }

@router.get("/supported-formats")
async def get_supported_formats():
    """
    지원하는 파일 형식 목록 반환
    """
    extensions = ProcessorFactory.get_supported_extensions()
    return BaseResponse(
        status=200,
        code="SUCCESS",
        message="지원하는 파일 형식 조회 성공",
        isSuccess=True,
        result=Result(data={
            "supported_extensions": extensions
        })
    )

@router.post("/extract-md", response_model=BaseResponse[dict])
async def extract_markdown(file: UploadFile = File(...)):
    """
    파일을 Markdown으로 변환
    - 파일 확장자 검증
    - 파일 업로드 및 저장
    - Markdown 변환 수행
    - 처리 시간 측정
    """

    # 파일명 검증
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="파일명이 없습니다."
        )
    
    file_service = FileService()
    t0 = time.perf_counter()
    saved_path = None

    try:
        # 파일 저장
        saved_path = file_service.save_uploaded_file(file)

        # 파일 확장자 검증 및 프로세서 가져오기
        try:
            processor = ProcessorFactory.get_processor(str(saved_path))
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": str(e),
                    "supported_extensions": ProcessorFactory.get_supported_extensions()
                }
            )
        
        # 파일 처리
        result = processor.process(str(saved_path))
        
        timing_sec = round(time.perf_counter() - t0, 3)

        return BaseResponse(
            status=200,
            code="SUCCESS",
            message="Markdown 추출 성공",
            isSuccess=True,
            result=Result(data={
                "file_path": str(saved_path),
                "filename": file.filename,
                "markdown": result["content"],
                "metadata": result.get("metadata", {}),
                "timing_sec": timing_sec,
            })
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"처리 중 오류가 발생했습니다: {str(e)}"
        )
    finally:
        # 파일 스트림 닫기
        try:
            file.file.close()
        except:
            pass
        
        # 임시 파일 삭제 (성공/실패 여부와 관계없이 항상 실행)
        if saved_path is not None:
            file_service.delete_file(saved_path)