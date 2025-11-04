from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from . import __version__, __title__, __description__
from .core.settings import settings
from .core.utils import custom_openapi

from .domains.file.routers.file_category import router as file_router
from .domains.image.routers.image_controller import router as image_router
from .domains.rag_setting.routers.strategy_router import router as rag_setting_router
from .domains.rag_setting.routers.ingest_router import router as ingest_router
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

app.include_router(file_router, prefix="/api/v1")
app.include_router(image_router, prefix="/api/v1")
app.include_router(rag_setting_router, prefix="/api/v1")
app.include_router(ingest_router, prefix="/api/v1")
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
