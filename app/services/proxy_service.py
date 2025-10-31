"""
Proxy service for forwarding requests to backend services
"""
import httpx
from fastapi import HTTPException
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


async def proxy_health_check(service_url: str, timeout: float = 5.0) -> Dict[str, Any]:
    """
    프록시 health check 서비스
    
    Args:
        service_url: 대상 서비스 URL
        timeout: 타임아웃 시간 (초)
    
    Returns:
        Health check 응답 JSON
        
    Raises:
        HTTPException: health check 실패 시
    """
    health_url = f"{service_url.rstrip('/')}/health"
    
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            response = await client.get(health_url)
            response.raise_for_status()
            return response.json()
        except httpx.TimeoutException:
            logger.warning(f"Health check timeout for {service_url}")
            raise HTTPException(
                status_code=504, 
                detail=f"Health check timeout for {service_url}"
            )
        except httpx.HTTPStatusError as e:
            logger.error(f"Health check failed for {service_url}: status={e.response.status_code}")
            # 보안: response.text 직접 노출 방지
            raise HTTPException(
                status_code=e.response.status_code, 
                detail=f"Health check failed: {e.response.text}"
            )
        except httpx.RequestError as e:
            logger.error(f"Request error for {service_url}: {str(e)}")
            raise HTTPException(
                status_code=502, 
                detail=f"Bad gateway: {str(e)}"
            )

