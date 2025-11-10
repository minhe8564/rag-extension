from fastapi import Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, Response
from typing import Optional
from urllib.parse import unquote
import httpx


async def proxy_service_docs(
    request: Request,
    service_url: str,
    base_prefix: str,  # e.g., "/service-docs/rag/extract"
    path: str = "",
    is_openapi: bool = False
):
    decoded_path = unquote(path) if path else ""
    if decoded_path and not decoded_path.startswith("/"):
        decoded_path = "/" + decoded_path

    target_url = f"{service_url}/openapi.json" if is_openapi else f"{service_url}{decoded_path}"

    query_string = str(request.url.query)
    if query_string:
        target_url = f"{target_url}?{query_string}"

    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            # 최소 헤더만 전달
            forwarded_headers = {
                key: value
                for key, value in request.headers.items()
                if key.lower() not in {"host", "content-length"}
            }
            headers = dict(forwarded_headers)

            # 본문 전달
            body: Optional[bytes] = None
            if request.method in ("POST", "PUT", "PATCH"):
                body = await request.body()

            resp = await client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                content=body,
            )

            # 응답 헤더 필터링
            response_headers = dict(resp.headers)
            response_headers.pop("host", None)
            response_headers.pop("content-encoding", None)
            response_headers.pop("transfer-encoding", None)
            response_headers.pop("content-length", None)

            # HTML (Swagger UI)인 경우 openapi 경로 치환
            content_type_header = resp.headers.get("content-type", "")
            if "text/html" in content_type_header:
                content = resp.text
                # 절대 경로 치환
                content = content.replace(
                    f"{service_url}/openapi.json",
                    f"{base_prefix}/openapi.json"
                )
                # 상대 경로 치환
                prefix_trimmed = base_prefix.lstrip("/")
                content = content.replace('"/openapi.json"', f'"/{prefix_trimmed}/openapi.json"')
                content = content.replace("'/openapi.json'", f"'/{prefix_trimmed}/openapi.json'")
                content = content.replace('url: "/openapi.json"', f'url: "/{prefix_trimmed}/openapi.json"')
                content = content.replace("url: '/openapi.json'", f"url: '/{prefix_trimmed}/openapi.json'")
                # OAuth redirect URL
                content = content.replace(
                    "/docs/oauth2-redirect",
                    f"{base_prefix}/docs/oauth2-redirect"
                )
                return HTMLResponse(content=content, headers=response_headers)

            # OpenAPI JSON이면 servers를 프록시 경로로 교체
            content_type = resp.headers.get("content-type", "")
            if is_openapi or content_type.startswith("application/json"):
                try:
                    data = resp.json()
                    if isinstance(data, dict) and "paths" in data:
                        data["servers"] = [{"url": "./api", "description": "RAG proxy"}]
                    return JSONResponse(content=data, status_code=resp.status_code, headers=response_headers)
                except Exception:
                    pass

            return Response(
                content=resp.content,
                status_code=resp.status_code,
                headers=response_headers,
                media_type=content_type
            )
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Service request timeout")
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Target service is unavailable")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Proxy error: {str(e)}")

