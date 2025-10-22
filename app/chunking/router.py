from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import StreamingResponse, Response
from starlette.background import BackgroundTask
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..database import get_db
from ..admin.models import BaseURL

router = APIRouter(prefix="/chunking", tags=["AI Chunking Service"])

HOP_BY_HOP_HEADERS = {
    "connection", "keep-alive", "proxy-authenticate", "proxy-authorization",
    "te", "trailers", "transfer-encoding", "upgrade"
}
SMALL_BODY_THRESHOLD = 1_000_000

async def _iter_request_body(request: Request):
    async for chunk in request.stream():
        yield chunk

@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"])
async def proxy_chunking(request: Request, path: str, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(BaseURL).where(BaseURL.service_name == "chunking"))
        base_url = result.scalar_one_or_none()
        
        if not base_url:
            raise HTTPException(status_code=503, detail="Chunking service URL not configured")
        
        target_url = f"{base_url.base_url}/{path}"

        headers = {
            k: v for k, v in request.headers.items()
            if k.lower() not in HOP_BY_HOP_HEADERS
        }
        headers.pop("host", None)
        headers.pop("accept-encoding", None)

        has_body = request.method not in {"GET", "HEAD"}
        content = _iter_request_body(request) if has_body else None

        async with httpx.AsyncClient(follow_redirects=False, timeout=None) as client:
            req = client.build_request(
                method=request.method,
                url=target_url,
                headers=headers,
                content=content,
                params=request.query_params  # httpx가 자동으로 URL 인코딩 처리
            )
            resp = await client.send(req, stream=True)

            filtered_headers = {
                k: v for k, v in resp.headers.items()
                if k.lower() not in HOP_BY_HOP_HEADERS and k.lower() != "content-length"
            }
            media_type = resp.headers.get("content-type")

            content_length = resp.headers.get("content-length")
            if content_length and content_length.isdigit() and int(content_length) <= SMALL_BODY_THRESHOLD:
                body = await resp.aread()
                return Response(content=body, status_code=resp.status_code, headers=filtered_headers, media_type=media_type)

            async def iter_resp():
                try:
                    async for chunk in resp.aiter_bytes():
                        yield chunk
                except (httpx.ReadError, httpx.StreamError):
                    return

            return StreamingResponse(
                iter_resp(),
                status_code=resp.status_code,
                headers=filtered_headers,
                media_type=media_type,
                background=BackgroundTask(resp.aclose)
            )

    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Chunking service timeout")
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Chunking service unavailable")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Proxy error: {str(e)}")