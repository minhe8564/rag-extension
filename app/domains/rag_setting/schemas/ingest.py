from __future__ import annotations

from typing import Dict, Any
from pydantic import BaseModel, Field


class IngestGroupListItem(BaseModel):
    """Ingest 그룹 목록 아이템"""
    ingestNo: str = Field(..., description="Ingest 그룹 ID (UUID)")
    isDefault: bool = Field(..., description="기본 템플릿 여부")
    extractionStrategy: Dict[str, Any] = Field(..., description="추출 전략 정보")
    chunkingStrategy: Dict[str, Any] = Field(..., description="청킹 전략 정보")
    embeddingStrategy: Dict[str, Any] = Field(..., description="임베딩 전략 정보")

    class Config:
        from_attributes = True
