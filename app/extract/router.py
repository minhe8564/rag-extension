from fastapi import APIRouter, Request, HTTPException
import httpx
from ..config import settings

router = APIRouter(
    prefix="/extract",
    tags=["AI Extract Service"]
)

@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"])
async def proxy_extract(request: Request, path: str):
    """
    Extract 서비스로 모든 요청 프록시
    """
    try:
        # 쿼리 파라미터 추가
        query_string = str(request.query_params) if request.query_params else ""
        target_url = f"{settings.extract_service_url}/{path}"
        if query_string:
            target_url = f"{target_url}?{query_string}"
        
        # 요청 헤더 준비
        headers = dict(request.headers)
        headers.pop("host", None)  # 호스트 헤더 제거
        
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                content=await request.body(),
                timeout=30.0
            )
            
            # JSON 응답인 경우만 .json() 사용
            if response.headers.get("content-type", "").startswith("application/json"):
                return response.json()
            else:
                return response.text
                
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Extract service timeout")
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Extract service unavailable")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Proxy error: {str(e)}")
