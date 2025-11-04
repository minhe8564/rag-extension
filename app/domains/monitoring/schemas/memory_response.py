"""
메모리 모니터링 응답 DTO
"""
from pydantic import BaseModel, Field


class MemoryUsageResponse(BaseModel):
    """
    메모리 사용량 응답 스키마
    """
    timestamp: str = Field(
        ...,
        description="이벤트 생성 시각 (ISO8601)",
        example="2025-11-03T18:10:00+09:00"
    )
    
    totalMemoryGB: float = Field(
        ...,
        description="총 메모리(GB)",
        ge=0.0,
        example=32.0
    )
    
    usedMemoryGB: float = Field(
        ...,
        description="현재 사용 중 메모리(GB)",
        ge=0.0,
        example=8.5
    )
    
    memoryUsagePercent: float = Field(
        ...,
        description="메모리 사용률(%)",
        ge=0.0,
        le=100.0,
        example=26.6
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": "2025-11-03T18:10:00+09:00",
                "totalMemoryGB": 32.0,
                "usedMemoryGB": 8.5,
                "memoryUsagePercent": 26.6
            }
        }

