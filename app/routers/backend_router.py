"""
Python Backend 프록시 라우터 및 서비스별 Swagger 문서 프록시
gateway.ragextension.shop/be/*
gateway.ragextension.shop/service-docs/*
"""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from ..services.proxy_service import proxy_request
from ..services.docs_service import proxy_docs_request
from ..core.settings import settings as app_settings
from urllib.parse import unquote

router = APIRouter(
    prefix="/be",
    tags=["Python Backend"]
)

# 서비스별 Swagger 문서 라우터 (prefix는 별도로 설정)
docs_router = APIRouter(
    prefix="/service-docs/be",
    tags=["Service Docs"]
)

@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
async def backend_proxy(request: Request, path: str):
    """
    /be/*로 들어오는 모든 요청을 python_backend_url로 프록시
    """
    return await proxy_request(
        request=request,
        target_url=app_settings.python_backend_url,
        path_prefix="/be"
    )


# 서비스별 Swagger 문서 엔드포인트
@docs_router.get("/docs", response_class=HTMLResponse)
async def get_service_docs(request: Request):
    """서비스의 Swagger UI 표시"""
    return await proxy_docs_request(request, "/docs")


@docs_router.get("/openapi.json")
async def get_service_openapi(request: Request):
    """서비스의 OpenAPI JSON 반환"""
    return await proxy_docs_request(request, "", is_openapi=True)


@docs_router.api_route("/api/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
async def proxy_service_api(request: Request, path: str):
    """서비스의 API 요청 프록시 (Swagger UI에서 요청 보낼 때 사용)"""
    # 경로 디코딩
    decoded_path = unquote(path)
    if not decoded_path.startswith("/"):
        decoded_path = "/" + decoded_path
    
    return await proxy_docs_request(request, decoded_path)

@docs_router.get("/")
async def redirect_to_docs():
    """서비스 이름만 입력하면 docs로 리다이렉트"""
    return RedirectResponse(url="/service-docs/be/docs")