"""RAG Setting domain HTTP routers."""
from fastapi import APIRouter

from .strategy_router import router as strategy_router

# Query 템플릿 라우터
from .query_create import router as query_create_router
from .query_read import router as query_read_router
from .query_update import router as query_update_router
from .query_delete import router as query_delete_router

# Ingest 템플릿 라우터
from .ingest_create import router as ingest_create_router
from .ingest_read import router as ingest_read_router
from .ingest_update import router as ingest_update_router
from .ingest_delete import router as ingest_delete_router

# Prompt 라우터
from .prompt_create import router as prompt_create_router
from .prompt_read import router as prompt_read_router
from .prompt_update import router as prompt_update_router
from .prompt_delete import router as prompt_delete_router


# RAG 도메인 전체를 하나의 라우터로 병합
rag_router = APIRouter()

# 전략 라우터 (prefix 제거하고 병합)
rag_router.include_router(strategy_router, prefix="", tags=["RAG - Strategy Management"])

# Query 템플릿 라우터들 (prefix 제거하고 병합)
rag_router.include_router(query_create_router, prefix="", tags=["RAG - Query Template Management"])
rag_router.include_router(query_read_router, prefix="", tags=["RAG - Query Template Management"])
rag_router.include_router(query_update_router, prefix="", tags=["RAG - Query Template Management"])
rag_router.include_router(query_delete_router, prefix="", tags=["RAG - Query Template Management"])

# Ingest 템플릿 라우터들 (prefix 제거하고 병합)
rag_router.include_router(ingest_create_router, prefix="", tags=["RAG - Ingest Template Management"])
rag_router.include_router(ingest_read_router, prefix="", tags=["RAG - Ingest Template Management"])
rag_router.include_router(ingest_update_router, prefix="", tags=["RAG - Ingest Template Management"])
rag_router.include_router(ingest_delete_router, prefix="", tags=["RAG - Ingest Template Management"])

# Prompt 라우터들 (prefix 제거하고 병합)
rag_router.include_router(prompt_create_router, prefix="", tags=["RAG - Prompt Management"])
rag_router.include_router(prompt_read_router, prefix="", tags=["RAG - Prompt Management"])
rag_router.include_router(prompt_update_router, prefix="", tags=["RAG - Prompt Management"])
rag_router.include_router(prompt_delete_router, prefix="", tags=["RAG - Prompt Management"])


__all__ = ["rag_router"]
