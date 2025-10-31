from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from . import __version__, __title__, __description__
from .config import settings
from datetime import datetime

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
