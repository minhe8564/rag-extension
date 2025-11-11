from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from . import __version__, __title__, __description__
from .config import settings
from .routers import router
from datetime import datetime
from .core.openapi import custom_openapi

app = FastAPI(
    title=__title__,
    description=__description__,
    version=__version__,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.openapi = lambda: custom_openapi(app)

# Router 등록
app.include_router(router)

@app.get("/")
async def root():
    return {
        "message": "Hebees Generation Service is running"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": __version__,
    }
