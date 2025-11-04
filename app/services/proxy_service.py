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
    
    # 요청 헤더 복사 (사용자 정보 헤더는 게이트웨이가 관리)
    forwarded_headers = {
        key: value
        for key, value in request.headers.items()
        if key.lower() not in {"x-user-role", "x-user-uuid"}
    }

    headers = dict(forwarded_headers)
    headers.pop("host", None)
    headers.pop("content-length", None)

    # 사용자 역할 정보 헤더 주입
    user_info = getattr(request.state, "user", None)
    if user_info and getattr(user_info, "is_authenticated", False):
        headers["x-user-role"] = str(user_info.role)
        headers["x-user-uuid"] = str(user_info.user_uuid)
    
    # 요청 본문 처리
    body: Optional[bytes] = None
    if request.method in ("POST", "PUT", "PATCH"):
        body = await request.body()
    
    # SSE 스트리밍 요청 감지 및 타임아웃 조정
    # HTTP 표준: Accept: text/event-stream 헤더로 SSE 요청 판단
    accept_header = request.headers.get("accept", "").lower()
    is_sse_stream = "text/event-stream" in accept_header
    
    # SSE 스트리밍일 경우 타임아웃을 무제한으로 설정
    if is_sse_stream:
        client_timeout = httpx.Timeout(
            connect=30.0,
            read=None,  # 무제한
            write=30.0,
            pool=30.0
        )
        logger.info(f"SSE 스트리밍 요청 감지 (Accept: text/event-stream): {target_path}, 타임아웃 무제한 설정")
    else:
        client_timeout = timeout
    
    # HTTP 메서드에 따라 요청
    async with httpx.AsyncClient(timeout=client_timeout) as client:
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
                except httpx.ReadError as e:
                    # SSE 스트리밍 중 연결이 끊어진 경우 정상 종료
                    # 클라이언트가 연결을 끊었거나 백엔드 서버가 스트림을 중단한 경우
                    if is_sse_stream:
                        logger.debug(f"SSE 스트리밍 연결이 끊어졌습니다: {target_path} - {str(e)}")
                        return  # 정상 종료
                    else:
                        # 일반 요청의 경우 에러로 처리
                        logger.error(f"프록시 응답 읽기 중 오류: {target_path} - {str(e)}")
                        raise
                except Exception as e:
                    logger.error(f"프록시 응답 스트림 중 오류: {target_path} - {str(e)}")
                    raise
                finally:
                    try:
                        await upstream_response.aclose()
                    except Exception as e:
                        logger.debug(f"업스트림 응답 닫기 중 오류 (무시): {str(e)}")

            return StreamingResponse(
                content=response_stream(),
                status_code=upstream_response.status_code,
                headers=response_headers,
                media_type=upstream_response.headers.get("content-type"),
            )
        except httpx.TimeoutException:
            logger.warning(f"프록시 요청이 시간 초과되었습니다: {target_url_full}")
            raise HTTPException(
                status_code=504,
                detail="게이트웨이 요청이 시간 초과되었습니다."
            )
        except httpx.RequestError as e:
            logger.error(f"프록시 요청 중 오류가 발생했습니다: {target_url_full} - {str(e)}")
            raise HTTPException(
                status_code=502,
                detail="게이트웨이 요청 처리 중 오류가 발생했습니다."
            )

