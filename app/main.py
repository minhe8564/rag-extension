from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from . import __version__, __title__, __description__
from .core.settings import settings
from .core.utils import custom_openapi
from .core.exception_handlers import register_exception_handlers

from .domains.file.routers.file_category import router as file_router
from .domains.file.routers.files import router as files_router
from .domains.file.routers.files_list import router as files_list_router
from .domains.file.routers.files_presigned import router as files_presigned_router
from .domains.file.routers.files_presigned_by_no import router as files_presigned_by_no_router
from .domains.collection.routers.collections import router as collections_router
from .domains.image.routers.image_controller import router as image_router
from .domains.rag_setting.routers import rag_router
from .domains.collection.routers.test_collection_router import router as test_collection_router
from .domains.monitoring.routers.monitoring_controller import router as monitoring_router
from datetime import datetime

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
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register global exception handlers (BaseResponse-style)
register_exception_handlers(app)

# File domain routers
app.include_router(file_router, prefix="/api/v1")
app.include_router(files_router, prefix="/api/v1")
app.include_router(files_list_router, prefix="/api/v1")
app.include_router(files_presigned_router, prefix="/api/v1")
app.include_router(files_presigned_by_no_router, prefix="/api/v1")

# Collection domain routers
app.include_router(collections_router, prefix="/api/v1")
app.include_router(test_collection_router, prefix="/api/v1")

# Image domain router
app.include_router(image_router, prefix="/api/v1")

# RAG Setting domain router (통합)
app.include_router(rag_router, prefix="/api/v1")

# Monitoring domain router
app.include_router(monitoring_router, prefix="/api/v1")

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
        "timestamp": datetime.now().isoformat(),
    }

