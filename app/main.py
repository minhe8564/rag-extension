from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from . import __version__, __title__, __description__
from .config import settings
from .admin import router as admin_router
from .extract import router as extract_router
from .chunking import router as chunking_router
import httpx
import logging

logger = logging.getLogger(__name__)

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

# 라우터 연결 - 공통 prefix /ai/api 추가
app.include_router(admin_router, prefix="/ai/api")
app.include_router(extract_router, prefix="/ai/api")
app.include_router(chunking_router, prefix="/ai/api")

@app.get("/")
async def root():
    return {
        "message": "Hebees API Gateway is running"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": __version__,
    }