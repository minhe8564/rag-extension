from fastapi import FastAPI
from . import __version__, __title__, __description__
from datetime import datetime

app = FastAPI(
    title=__title__,
    description=__description__,
    version=__version__,
)

@app.get("/")
async def root():
    return {
        "message": "Hebees Search Service is running"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": __version__,
    }
