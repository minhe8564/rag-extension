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
        # Longer timeouts for potentially long-running operations (query/process, etc.)
        timeout = httpx.Timeout(connect=30.0, read=3600.0, write=120.0, pool=30.0)
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            # 요청 헤더 복사 (사용자 정보 헤더는 게이트웨이가 관리)
            forwarded_headers = {
                key: value
                for key, value in request.headers.items()
                if key.lower() not in {"x-user-role", "x-user-uuid", "host", "content-length"}
            }

            headers = dict(forwarded_headers)

            # 사용자 역할 정보 헤더 주입 (JWT 토큰 처리)
            user_info = getattr(request.state, "user", None)
            if user_info and getattr(user_info, "is_authenticated", False):
                headers["x-user-role"] = str(user_info.role)
                headers["x-user-uuid"] = str(user_info.user_uuid)
            
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
                        # 상대 경로를 사용하여 Swagger가 현재 origin으로 인식하도록 함 (JWT 자동 적용)
                        data["servers"] = [{"url": "./api", "description": "Gateway proxy"}]
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



async def proxy_service_docs(
    request: Request,
    service_url: str,
    service_key: str,
    path: str = "",
    is_openapi: bool = False,
    public_prefix: str | None = None
):
    """일반화된 서비스 Swagger 프록시 (service_key에 따라 경로 치환)"""
    decoded_path = unquote(path) if path else ""
    if decoded_path and not decoded_path.startswith("/"):
        decoded_path = "/" + decoded_path

    # OpenAPI 요청은 전달된 경로가 있으면 그것을 우선 사용
    if is_openapi:
        target_url = f"{service_url}{decoded_path if decoded_path else '/openapi.json'}"
    else:
        target_url = f"{service_url}{decoded_path}"

    query_string = str(request.url.query)
    if query_string:
        target_url = f"{target_url}?{query_string}"

    try:
        # Longer timeouts for nested docs API calls (e.g., /service-docs/rag/api/*)
        timeout = httpx.Timeout(connect=30.0, read=3600.0, write=120.0, pool=30.0)
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            forwarded_headers = {
                key: value
                for key, value in request.headers.items()
                if key.lower() not in {"x-user-role", "x-user-uuid", "host", "content-length"}
            }
            headers = dict(forwarded_headers)
            user_info = getattr(request.state, "user", None)
            if user_info and getattr(user_info, "is_authenticated", False):
                headers["x-user-role"] = str(user_info.role)
                headers["x-user-uuid"] = str(user_info.user_uuid)

            body: Optional[bytes] = None
            if request.method in ("POST", "PUT", "PATCH"):
                body = await request.body()

            response = await client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                content=body,
            )

            response_headers = dict(response.headers)
            response_headers.pop("host", None)
            response_headers.pop("content-encoding", None)
            response_headers.pop("transfer-encoding", None)
            response_headers.pop("content-length", None)

            content_type_header = response.headers.get("content-type", "")
            if "text/html" in content_type_header:
                # HTML 내 openapi.json 참조를 게이트웨이 공개 경로로 rewrite
                content = response.text
                # UI가 참조해야 하는 공개 prefix 계산
                if public_prefix:
                    base = public_prefix
                else:
                    req_path = request.url.path
                    if req_path.endswith("/docs"):
                        base = req_path[: -len("/docs")]
                    elif req_path.endswith("/openapi.json"):
                        base = req_path[: -len("/openapi.json")]
                    else:
                        base = f"/service-docs/{service_key}"
                # 절대경로 {service_url}/openapi.json -> {base}/openapi.json
                content = content.replace(
                    f"{service_url}/openapi.json",
                    f"{base}/openapi.json"
                )
                # 상대경로 "/openapi.json" -> "{base}/openapi.json"
                content = content.replace('"/openapi.json"', f'"{base}/openapi.json"')
                content = content.replace("'/openapi.json'", f"'{base}/openapi.json'")
                content = content.replace('url: "/openapi.json"', f'url: "{base}/openapi.json"')
                content = content.replace("url: '/openapi.json'", f"url: '{base}/openapi.json'")
                # ingest가 '/service-docs/{service}/openapi.json'을 사용한다면, 게이트웨이 공개 경로로 보정
                if base.startswith("/rag/"):
                    content = content.replace('"/service-docs/', '"/rag/service-docs/')
                    content = content.replace("'/service-docs/", "'/rag/service-docs/")
                    content = content.replace('url: "/service-docs/', 'url: "/rag/service-docs/')
                    content = content.replace("url: '/service-docs/", "url: '/rag/service-docs/")
                else:
                    # 절대 ingest URL을 게이트웨이 공개 경로로 축약: {ingest_url}/service-docs/* -> /service-docs/*
                    content = content.replace(f'"{service_url}/service-docs/', '"/service-docs/')
                    content = content.replace(f"'{service_url}/service-docs/", "'/service-docs/")
                    content = content.replace(f'url: "{service_url}/service-docs/', 'url: "/service-docs/')
                    content = content.replace(f"url: '{service_url}/service-docs/", "url: '/service-docs/")
                # OAuth redirect URL도 공개 경로 기준으로 변경
                content = content.replace(
                    "/docs/oauth2-redirect",
                    f"{base}/docs/oauth2-redirect"
                )
                return HTMLResponse(content=content, headers=response_headers)

            content_type = response.headers.get("content-type", "")
            if is_openapi or content_type.startswith("application/json"):
                try:
                    data = response.json()
                    if isinstance(data, dict) and "paths" in data:
                        data["servers"] = [{"url": "./api", "description": "Gateway proxy"}]
                    return JSONResponse(content=data, status_code=response.status_code, headers=response_headers)
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
        raise HTTPException(status_code=503, detail="Service is unavailable")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Proxy error: {str(e)}")