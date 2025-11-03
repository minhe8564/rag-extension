from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from . import __version__, __title__, __description__
from .config import settings
from .utils import custom_openapi
from .routers import access_router, file_category_router
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

# Include application routers
app.include_router(access_router.router)
app.include_router(file_category_router.router)

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
