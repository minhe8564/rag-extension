"""
Swagger 문서 프록시 서비스
"""
from fastapi import Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, Response
from ..core.settings import settings as app_settings
import httpx
from typing import Optional
from urllib.parse import unquote


async def proxy_docs_request(
    request: Request,
    path: str = "",
    is_openapi: bool = False
):
    """서비스의 Swagger 문서 또는 API 요청 프록시"""
    service_url = app_settings.python_backend_url
    
    # 경로 디코딩
    decoded_path = unquote(path) if path else ""
    if decoded_path and not decoded_path.startswith("/"):
        decoded_path = "/" + decoded_path
    
    # OpenAPI JSON 요청
    if is_openapi:
        target_url = f"{service_url}/openapi.json"
    else:
        target_url = f"{service_url}{decoded_path}"
    
    # 쿼리 파라미터 포함
    query_string = str(request.url.query)
    if query_string:
        target_url = f"{target_url}?{query_string}"
    
    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            # 요청 헤더 복사
            headers = {
                key: value
                for key, value in request.headers.items()
                if key.lower() not in {"host", "content-length"}
            }
            
            # 요청 본문 처리
            body: Optional[bytes] = None
            if request.method in ("POST", "PUT", "PATCH"):
                body = await request.body()
            
            # 요청 전송
            response = await client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                content=body,
            )
            
            # 응답 헤더 필터링
            response_headers = dict(response.headers)
            response_headers.pop("host", None)
            response_headers.pop("content-encoding", None)
            response_headers.pop("transfer-encoding", None)
            response_headers.pop("content-length", None)
            
            # Swagger UI HTML인 경우 base URL 수정
            content_type_header = response.headers.get("content-type", "")
            if "text/html" in content_type_header:
                content = response.text
                
                # 절대 경로 교체
                content = content.replace(
                    f'{service_url}/openapi.json',
                    f'/service-docs/be/openapi.json'
                )
                
                # 상대 경로 교체 (★ 이게 중요)
                content = content.replace(
                    '"/openapi.json"',
                    f'"/service-docs/be/openapi.json"'
                )
                content = content.replace(
                    "'/openapi.json'",
                    f"'/service-docs/be/openapi.json'"
                )
                content = content.replace(
                    'url: "/openapi.json"',
                    f'url: "/service-docs/be/openapi.json"'
                )
                content = content.replace(
                    "url: '/openapi.json'",
                    f"url: '/service-docs/be/openapi.json'"
                )
                
                # OAuth redirect URL도 안전하게 변경
                content = content.replace(
                    "/docs/oauth2-redirect",
                    f"/service-docs/be/docs/oauth2-redirect"
                )
                
                return HTMLResponse(content=content, headers=response_headers)
            
            # JSON 응답인 경우 OpenAPI 스펙의 servers URL 수정
            content_type = response.headers.get("content-type", "")
            if is_openapi or content_type.startswith("application/json"):
                try:
                    data = response.json()
                    if isinstance(data, dict) and "paths" in data:  # OpenAPI 스펙 확인
                        # Swagger UI가 게이트웨이를 통해 요청을 보낼 수 있도록 서버 URL 설정
                        data["servers"] = [{"url": f"/service-docs/be/api", "description": "Gateway proxy"}]
                    return JSONResponse(
                        content=data,
                        status_code=response.status_code,
                        headers=response_headers
                    )
                except:
                    pass
            
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=response_headers,
                media_type=content_type
            )
            
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Service request timeout")
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Python Backend is unavailable")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Proxy error: {str(e)}")

