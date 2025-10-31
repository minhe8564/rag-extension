"""
Main FastAPI application
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from . import __version__, __title__, __description__
from .core.settings import settings
from .core.utils import custom_openapi
from .common.auth.middleware import jwt_auth_middleware
from .routers import rag_router
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
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# JWT 인증 미들웨어
@app.middleware("http")
async def jwt_auth_middleware_handler(request: Request, call_next):
    return await jwt_auth_middleware(request, call_next)

# Include routers
app.include_router(rag_router.router)

@app.get("/health")
async def health_check():
    """기본 헬스체크"""
    return {
        "status": "healthy",
        "version": __version__
    }