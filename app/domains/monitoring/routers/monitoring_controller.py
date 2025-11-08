"""
시스템 모니터링 API 컨트롤러
CPU 사용률 등 시스템 리소스 모니터링
"""
from fastapi import APIRouter, Header, HTTPException, status, Depends
from fastapi.responses import StreamingResponse
from typing import Optional, AsyncIterator, Callable
import logging

from app.core.auth.check_role import check_role
from app.core.config.settings import settings
from ..services.monitoring_service import MonitoringService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/monitoring",
    tags=["Monitoring"]
)


def get_monitoring_service() -> MonitoringService:
    try:
        return MonitoringService()
    except ImportError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="시스템 모니터링 기능을 사용할 수 없습니다. psutil이 설치되지 않았습니다."
        )


def create_sse_streaming_response(
    stream_generator: Callable[[], AsyncIterator[str]],
    error_message: str
) -> StreamingResponse:
    try:
        async def generate():
            async for event in stream_generator():
                yield event
        
        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"{error_message}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"{error_message}: {str(e)}"
        )


@router.get("/cpu/stream")
async def stream_cpu_usage(
    x_user_role: str = Depends(check_role("ADMIN")),
    accept: Optional[str] = Header(None, alias="Accept"),
    cache_control: Optional[str] = Header(None, alias="Cache-Control"),
):
    # Accept 헤더 확인
    if accept and "text/event-stream" not in accept:
        logger.warning(f"Accept 헤더가 text/event-stream이 아닙니다: {accept}")
    
    monitoring_service = get_monitoring_service()
    return create_sse_streaming_response(
        stream_generator=monitoring_service.stream_cpu_usage,
        error_message="CPU 사용률 스트리밍 중 오류가 발생했습니다"
    )


@router.get("/memory/stream")
async def stream_memory_usage(
    x_user_role: str = Depends(check_role("ADMIN")),
    accept: Optional[str] = Header(None, alias="Accept"),
    cache_control: Optional[str] = Header(None, alias="Cache-Control"),
):
    # Accept 헤더 확인
    if accept and "text/event-stream" not in accept:
        logger.warning(f"Accept 헤더가 text/event-stream이 아닙니다: {accept}")
    
    monitoring_service = get_monitoring_service()
    return create_sse_streaming_response(
        stream_generator=monitoring_service.stream_memory_usage,
        error_message="메모리 사용량 스트리밍 중 오류가 발생했습니다"
    )


@router.get("/network/stream")
async def stream_network_traffic(
    x_user_role: str = Depends(check_role("ADMIN")),
    accept: Optional[str] = Header(None, alias="Accept"),
    cache_control: Optional[str] = Header(None, alias="Cache-Control"),
):
    # Accept 헤더 확인
    if accept and "text/event-stream" not in accept:
        logger.warning(f"Accept 헤더가 text/event-stream이 아닙니다: {accept}")
    
    monitoring_service = get_monitoring_service()
    
    async def network_stream_generator():
        async for event in monitoring_service.stream_network_traffic(bandwidth_mbps=None):
            yield event
    
    return create_sse_streaming_response(
        stream_generator=network_stream_generator,
        error_message="네트워크 트래픽 스트리밍 중 오류가 발생했습니다"
    )

