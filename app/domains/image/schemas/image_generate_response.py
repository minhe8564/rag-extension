"""
이미지 생성 응답 DTO
"""
from pydantic import BaseModel, Field
from datetime import datetime
from .image_response import ImageResponse


class ImageGenerateResponse(BaseModel):
    """
    이미지 생성 응답 스키마
    """
    status: str = Field(
        ...,
        description="생성 상태",
        example="success"
    )
    
    images: list[ImageResponse] = Field(
        ...,
        description="생성된 이미지 목록",
        default_factory=list
    )
    
    created_at: datetime = Field(
        ...,
        description="생성 완료 시간",
        example="2025-01-03T12:34:56"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "images": [
                    {
                        "image_id": "a1b2c3d4e5f6789012345678901234",
                        "url": "http://localhost:9000/image/s407/1q2w3e4r/generated/abc123.png",
                        "type": "png"
                    }
                ],
                "created_at": "2025-11-03 12:15:37"
            }
        }
