"""
네트워크 트래픽 모니터링 응답 DTO
"""
from pydantic import BaseModel, Field


class NetworkTrafficResponse(BaseModel):
    """
    네트워크 트래픽 응답 스키마
    """
    timestamp: str = Field(
        ...,
        description="이벤트 생성 시각 (ISO8601)",
        example="2025-11-03T18:20:00+09:00"
    )
    
    inboundMbps: float = Field(
        ...,
        description="실시간 Inbound 속도(Mbps)",
        ge=0.0,
        example=12.4
    )
    
    outboundMbps: float = Field(
        ...,
        description="실시간 Outbound 속도(Mbps)",
        ge=0.0,
        example=8.7
    )
    
    bandwidthMbps: float = Field(
        ...,
        description="네트워크 총 대역폭(Mbps)",
        ge=0.0,
        example=1000.0
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": "2025-11-03T18:20:00+09:00",
                "inboundMbps": 12.4,
                "outboundMbps": 8.7,
                "bandwidthMbps": 1000.0
            }
        }

