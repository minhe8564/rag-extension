from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from . import __version__, __title__, __description__
from .config import settings
from .routers import admin
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

app.include_router(admin.router)

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