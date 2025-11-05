from fastapi import FastAPI
from app.config import settings

app = FastAPI(title=settings.app_name, version="0.1.0")


@app.get("/")
async def root():
    return {"message": "Hello from RAG Data Marker!"}


@app.get("/health")
async def health():
    return {"status": "healthy"}

