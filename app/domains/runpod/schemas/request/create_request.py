from __future__ import annotations

from pydantic import BaseModel, Field


class RunpodCreateRequest(BaseModel):
    """Runpod 생성 요청 스키마"""
    name: str = Field(..., description="Runpod 이름", min_length=1, max_length=255)
    address: str = Field(..., description="Runpod 주소", min_length=1, max_length=500)

