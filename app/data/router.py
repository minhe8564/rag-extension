from fastapi import APIRouter
import httpx
from ..config import settings

router = APIRouter(
    prefix="/data",
    tags=["AI Data Processing Pipeline"]
)

@router.post("/extract")
async def extract_data():
    """문서 추출"""
    async with httpx.AsyncClient() as client:
        response = await client.post(settings.extract_service_url)
        return response.json()

@router.post("/chunk")
async def chunk_data():
    """청킹"""
    async with httpx.AsyncClient() as client:
        response = await client.post(settings.chunking_service_url)
        return response.json()

@router.post("/embed")
async def embed_data():
    """임베딩"""
    async with httpx.AsyncClient() as client:
        response = await client.post(settings.embedding_service_url)
        return response.json()
