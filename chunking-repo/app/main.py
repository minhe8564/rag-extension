from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from . import __version__, __title__, __description__
from .routers import router
from .config import settings
from datetime import datetime
from typing import Dict, Any
from .core.openapi import custom_openapi

app = FastAPI(
    title=__title__,
    description=__description__,
    version=__version__,
)

app.openapi = lambda: custom_openapi(app)

# Router 등록
app.include_router(router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "Hebees Chunking Service is running"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": __version__,
    }
