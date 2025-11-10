"""
RAG Orchestrator 프록시 라우터
gateway.ragextension.shop/rag/*
"""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from ..services.proxy_service import proxy_request
from ..services.docs_service import proxy_service_docs
from ..core.settings import settings as app_settings
from urllib.parse import unquote
import httpx

router = APIRouter(
    prefix="/rag",
    tags=["RAG Orchestrator"]
)


@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
async def rag_proxy(request: Request, path: str):
    """
    /rag/*로 들어오는 모든 요청을 rag_orchestrator_url로 프록시
    """
    return await proxy_request(
        request=request,
        target_url=app_settings.rag_orchestrator_url,
        path_prefix="/rag"
    )

# -----------------------------
# Service Docs router (merged like backend_router.docs_router)
# -----------------------------

docs_router = APIRouter(
    prefix="/service-docs/rag",
    tags=["Service Docs - RAG"]
)

@docs_router.get("/docs", response_class=HTMLResponse)
async def get_ingest_docs(request: Request):
    return await proxy_service_docs(
        request=request,
        service_url=app_settings.rag_orchestrator_url,
        service_key="rag",
        path="/docs",
        public_prefix=""
    )

@docs_router.get("/openapi.json")
async def get_ingest_openapi(request: Request):
    return await proxy_service_docs(
        request=request,
        service_url=app_settings.rag_orchestrator_url,
        service_key="rag",
        path="/openapi.json",
        is_openapi=True,
        public_prefix=""
    )

@docs_router.api_route("/api/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
async def proxy_ingest_api(request: Request, path: str):
    decoded_path = unquote(path)
    if not decoded_path.startswith("/"):
        decoded_path = "/" + decoded_path
    return await proxy_service_docs(
        request=request,
        service_url=app_settings.rag_orchestrator_url,
        service_key="rag",
        path=f"/{decoded_path}"
    )

# Nested service docs under /rag/service-docs/{service}
# This ensures HTML is rewritten to /rag/service-docs/{service}/openapi.json
nested_docs_router = APIRouter(
    prefix="/rag/service-docs",
    tags=["Service Docs - Nested"]
)

@nested_docs_router.get("/{service}/docs", response_class=HTMLResponse)
async def get_nested_service_docs(service: str, request: Request):
    # 공개 경로를 게이트웨이 기준으로 매핑: /rag/service-docs/{service}/~
    public_prefix = f"/rag/service-docs/{service}"
    return await proxy_service_docs(
        request=request,
        service_url=app_settings.rag_orchestrator_url,
        service_key="rag",
        path=f"/service-docs/{service}/docs",
        public_prefix=public_prefix
    )

@nested_docs_router.get("/{service}/openapi.json")
async def get_nested_service_openapi(service: str, request: Request):
    return await proxy_service_docs(
        request=request,
        service_url=app_settings.rag_orchestrator_url,
        service_key="rag",
        path=f"/service-docs/{service}/openapi.json",
        is_openapi=True
    )

@nested_docs_router.api_route("/{service}/api/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
async def proxy_nested_service_api(service: str, path: str, request: Request):
    decoded_path = unquote(path)
    if not decoded_path.startswith("/"):
        decoded_path = "/" + decoded_path
    return await proxy_service_docs(
        request=request,
        service_url=app_settings.rag_orchestrator_url,
        service_key="rag",
        path=f"/service-docs/{service}/api{decoded_path}"
    )


