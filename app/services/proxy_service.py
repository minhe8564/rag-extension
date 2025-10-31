import httpx
from fastapi import HTTPException, Request
from fastapi.responses import StreamingResponse
from typing import AsyncIterator, Optional
import logging

logger = logging.getLogger(__name__)


async def proxy_request(
    request: Request,
    target_url: str,
    path_prefix: str = "",
    timeout: float = 30.0
):
    """
    범용 프록시 서비스 - 모든 HTTP 메서드 지원
    대용량 응답을 효율적으로 처리하기 위해 스트리밍 방식을 사용
    """
    # 경로에서 prefix 제거
    original_path = request.url.path
    if path_prefix and original_path.startswith(path_prefix):
        target_path = original_path[len(path_prefix):]
    else:
        target_path = original_path
    
    # 쿼리 파라미터 포함
    query_string = str(request.url.query)
    if query_string:
        target_url_full = f"{target_url.rstrip('/')}{target_path}?{query_string}"
    else:
        target_url_full = f"{target_url.rstrip('/')}{target_path}"
    
    # 요청 헤더 복사
    headers = dict(request.headers)
    headers.pop("host", None)
    headers.pop("content-length", None)
    
    # 요청 본문 처리
    body: Optional[bytes] = None
    if request.method in ("POST", "PUT", "PATCH"):
        body = await request.body()
    
    # HTTP 메서드에 따라 요청
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            upstream_request = client.build_request(
                method=request.method,
                url=target_url_full,
                headers=headers,
                content=body,
            )

            upstream_response = await client.send(upstream_request, stream=True)

            # 응답 헤더 필터링
            response_headers = dict(upstream_response.headers)
            response_headers.pop("host", None)
            response_headers.pop("content-encoding", None)
            response_headers.pop("transfer-encoding", None)
            response_headers.pop("content-length", None)

            async def response_stream() -> AsyncIterator[bytes]:
                try:
                    async for chunk in upstream_response.aiter_bytes():
                        yield chunk
                finally:
                    await upstream_response.aclose()

            return StreamingResponse(
                content=response_stream(),
                status_code=upstream_response.status_code,
                headers=response_headers,
                media_type=upstream_response.headers.get("content-type"),
            )
        except httpx.TimeoutException:
            logger.warning(f"Proxy timeout for {target_url_full}")
            raise HTTPException(
                status_code=504,
                detail="Gateway timeout"
            )
        except httpx.RequestError as e:
            logger.error(f"Proxy request error for {target_url_full}: {str(e)}")
            raise HTTPException(
                status_code=502,
                detail="Bad gateway"
            )

