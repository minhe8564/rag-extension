"""
Main FastAPI application
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from . import __version__, __title__, __description__
from .core.settings import settings
from .core.utils import custom_openapi
from .common.auth.middleware import jwt_auth_middleware
from .routers import rag_router, backend_router
import logging

logger = logging.getLogger(__name__)

app = FastAPI(
    title=__title__,
    description=__description__,
    version=__version__,
    swagger_ui_parameters={
        "persistAuthorization": True,
    }
)

app.openapi_schema = None

# Custom OpenAPI schema
app.openapi = lambda: custom_openapi(app)

# CORS 미들웨어
cors_kwargs = {
    "allow_credentials": True,
    "allow_methods": ["*"],
    "allow_headers": ["*"],
}

# 일반 도메인
if settings.allowed_origins_list:
    cors_kwargs["allow_origins"] = settings.allowed_origins_list

# 와일드카드 도메인 (정규식)
if settings.allowed_origin_regex_list:
    cors_kwargs["allow_origin_regex"] = "|".join(settings.allowed_origin_regex_list)

app.add_middleware(CORSMiddleware, **cors_kwargs)

# JWT 인증 미들웨어
@app.middleware("http")
async def jwt_auth_middleware_handler(request: Request, call_next):
    return await jwt_auth_middleware(request, call_next)

# Include routers (docs_router를 먼저 등록하여 /service-docs 경로가 FastAPI 기본 /docs보다 우선되도록)
app.include_router(backend_router.docs_router)
app.include_router(rag_router.docs_router)
app.include_router(rag_router.nested_docs_router)
app.include_router(rag_router.router)
app.include_router(backend_router.router)

@app.get("/health")
async def health_check():
    """기본 헬스체크"""
    return {
        "status": "healthy",
        "version": __version__
    }