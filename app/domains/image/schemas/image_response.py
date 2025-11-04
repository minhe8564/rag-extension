"""
이미지 정보 응답 DTO
"""
from pydantic import BaseModel, Field


class ImageResponse(BaseModel):
    """
    이미지 정보 응답 스키마
    단일 이미지 정보를 반환
    """
    image_id: str = Field(
        ...,
        description="이미지 ID (FILE_NO)",
        example="a1b2c3d4e5f6789012345678901234"
    )
    
    url: str = Field(
        ...,
        description="MinIO에서 제공하는 이미지 URL",
        example="http://localhost:9000/image/s407/1q2w3e4r/generated/abc123.png"
    )
    
    type: str = Field(
        ...,
        description="파일 타입",
        example="png"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "image_id": "a1b2c3d4e5f6789012345678901234",
                "url": "http://localhost:9000/image/s407/1q2w3e4r/generated/abc123.png",
                "type": "png"
            }
        }
