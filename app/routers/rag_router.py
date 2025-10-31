"""
RAG Orchestrator 프록시 라우터
gateway.ragextension.shop/rag/health
"""
from fastapi import APIRouter
from ..services.proxy_service import proxy_health_check
from ..core.settings import settings as app_settings

router = APIRouter(
    prefix="/rag",
    tags=["RAG Orchestrator"]
)


@router.get("/health")
async def rag_health_check():
    """
    /rag/health로 들어오면 rag_orchestrator_url/health로 프록시
    """
    return await proxy_health_check(app_settings.rag_orchestrator_url)

