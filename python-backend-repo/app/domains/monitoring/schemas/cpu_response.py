"""
CPU 모니터링 응답 DTO
"""
from pydantic import BaseModel, Field
from typing import Optional


class CpuUsageResponse(BaseModel):
    """
    CPU 사용률 응답 스키마
    """
    timestamp: str = Field(
        ...,
        description="이벤트 생성 시각 (ISO8601)",
        example="2025-11-03T17:55:12+09:00"
    )
    
    cpuUsagePercent: float = Field(
        ...,
        description="CPU 사용률 (%)",
        ge=0.0,
        le=100.0,
        example=12.3
    )
    
    totalCores: int = Field(
        ...,
        description="총 CPU 코어 수",
        ge=1,
        example=16
    )
    
    activeCores: int = Field(
        ...,
        description="현재 사용 중으로 추정되는 코어 수",
        ge=0,
        example=2
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": "2025-11-03T17:55:12+09:00",
                "cpuUsagePercent": 12.3,
                "totalCores": 16,
                "activeCores": 2
            }
        }

