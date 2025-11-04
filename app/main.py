from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from . import __version__, __title__, __description__
from .common.config import settings
from .common.utils.openapi import custom_openapi

from .routers.file_category_router import router as file_category_router_router
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

app.include_router(file_category_router_router)

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
