from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from . import __version__, __title__, __description__
from .core.config.settings import settings
from .core.utils.utils import custom_openapi
from .core.exceptions.exception_handlers import register_exception_handlers

from .domains.file.routers.file_category import router as file_router
from .domains.file.routers.file_upload import router as files_router
from .domains.file.routers.file_list import router as files_list_router
from .domains.file.routers.file_presigned import router as files_presigned_router
from .domains.file.routers.file_presigned_by_no import router as files_presigned_by_no_router
from .domains.file.routers.file_delete import router as files_delete_router
from .domains.collection.routers.collections import router as collections_router
from .domains.image.routers.image_controller import router as image_router
from .domains.rag_setting.routers import rag_router
from .domains.test.routers.test_collection_router import router as test_collection_router
from .domains.monitoring.routers.monitoring_controller import router as monitoring_router
from .domains.runpod.routers.runpod_controller import router as runpod_router
from .domains.sales_report.routers.sales_reports import router as sales_report_router
from .core.utils.timezone_utils import now_kst

app = FastAPI(
    title=__title__,
    description=__description__,
    version=__version__,
    swagger_ui_parameters={
        "persistAuthorization": True,
    },
)

app.openapi_schema = None
app.openapi = lambda: custom_openapi(app)

# CORS 설정
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

# Register global exception handlers (BaseResponse-style)
register_exception_handlers(app)

# File domain routers
app.include_router(file_router, prefix="/api/v1")
app.include_router(files_router, prefix="/api/v1")
app.include_router(files_list_router, prefix="/api/v1")
app.include_router(files_presigned_router, prefix="/api/v1")
app.include_router(files_presigned_by_no_router, prefix="/api/v1")
app.include_router(files_delete_router, prefix="/api/v1")

# Collection domain routers
app.include_router(collections_router, prefix="/api/v1")
app.include_router(test_collection_router, prefix="/api/v1")

# Image domain router
app.include_router(image_router, prefix="/api/v1")

# RAG Setting domain router (통합)
app.include_router(rag_router, prefix="/api/v1")

# Monitoring domain router
app.include_router(monitoring_router, prefix="/api/v1")
app.include_router(runpod_router, prefix="/api/v1")

# Sales Report domain router
app.include_router(sales_report_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {
        "message": "Hebees Python Backend Service is running",
        "app_name": settings.app_name,
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": __version__,
        "timestamp": now_kst().isoformat(),
    }

