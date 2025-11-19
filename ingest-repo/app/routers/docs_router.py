from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from app.service.docs_proxy import proxy_service_docs
from app.core.settings import settings
import httpx

router = APIRouter(prefix="/service-docs", tags=["Service Docs - RAG"])

# Downstream services via ingest
def _svc(rel_prefix: str, target_url: str):
    # rel_prefix: e.g., "extract"
    router_prefix = f"/{rel_prefix.lstrip('/')}"
    # 컨테이너(ingest) 내부 기준 경로로 HTML을 구성하고, 게이트웨이가 공개 경로로 rewrite
    base_prefix = f"/service-docs{router_prefix}"
    svc_router = APIRouter(prefix=router_prefix)

    @svc_router.get("/docs", response_class=HTMLResponse, include_in_schema=False, name=f"{rel_prefix}_docs_ui")
    async def docs(request: Request):
        return await proxy_service_docs(request, target_url, base_prefix, "/docs")

    @svc_router.get("/openapi.json", include_in_schema=False, name=f"{rel_prefix}_openapi_json")
    async def openapi(request: Request):
        return await proxy_service_docs(request, target_url, base_prefix, is_openapi=True)

    @svc_router.api_route(
        "/api/{path:path}",
        methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"],
        include_in_schema=False,
        name=f"{rel_prefix}_proxy_api"
    )
    async def api(request: Request, path: str):
        return await proxy_service_docs(request, target_url, base_prefix, f"/{path}")

    return svc_router

router.include_router(_svc("extract", settings.extract_service_url))
router.include_router(_svc("chunking", settings.chunking_service_url))
router.include_router(_svc("embedding", settings.embedding_service_url))
router.include_router(_svc("query-embedding", settings.query_embedding_service_url))
router.include_router(_svc("search", settings.search_service_url))
router.include_router(_svc("cross-encoder", settings.cross_encoder_service_url))
router.include_router(_svc("generation", settings.generation_service_url))



