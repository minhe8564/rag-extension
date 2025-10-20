from fastapi import APIRouter
import httpx
from ..config import settings

router = APIRouter(
    prefix="/chat",
    tags=["AI Chat Pipeline"]
)

@router.post("/query")
async def query_embedding():
    """쿼리 임베딩"""
    async with httpx.AsyncClient() as client:
        response = await client.post(settings.query_embedding_service_url)
        return response.json()

@router.post("/search")
async def search_documents():
    """문서 검색"""
    async with httpx.AsyncClient() as client:
        response = await client.post(settings.search_service_url)
        return response.json()

@router.post("/rerank")
async def rerank_documents():
    """문서 리랭킹"""
    async with httpx.AsyncClient() as client:
        response = await client.post(settings.cross_encoder_service_url)
        return response.json()

@router.post("/generate")
async def generate_response():
    """응답 생성"""
    async with httpx.AsyncClient() as client:
        response = await client.post(settings.generation_service_url)
        return response.json()
