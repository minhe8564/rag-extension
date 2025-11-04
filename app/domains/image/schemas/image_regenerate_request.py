"""
이미지 재생성 요청 DTO
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from .image_request import ImageSize, ALLOWED_IMAGE_SIZES


class ImageRegenerateRequest(BaseModel):
    image_id: str = Field(
        ...,
        description="재생성할 원본 이미지 ID (UUID)",
        example="cf8309267cdc41b9b472d7cbfc13682b"
    )

    prompt: Optional[str] = Field(
        default=None,
        description="새로운 프롬프트 (미제공 시 기존 프롬프트 사용)",
        examples=["포근한 크리스마스 분위기의 일러스트, 눈 내리는 마을, 트리와 선물 상자, 따뜻한 조명, 포스터 스타일"]
    )

    size: Optional[ImageSize] = Field(
        default=None,
        description="이미지 크기 (허용된 비율만 가능, 미제공 시 기존 크기 사용)",
        examples=["1024x1024", "1344x768", "832x1248"]
    )

    style: Optional[str] = Field(
        default=None,
        description="이미지 스타일 (미제공 시 기존 스타일 사용)",
        example="realistic"
    )

    @field_validator("size")
    @classmethod
    def validate_size(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ALLOWED_IMAGE_SIZES:
            raise ValueError(
                f"허용되지 않은 이미지 크기입니다. "
                f"허용된 크기: {', '.join(ALLOWED_IMAGE_SIZES)}"
            )
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "image_id": "cf8309267cdc41b9b472d7cbfc13682b",
                "prompt": "A new prompt for regeneration",
                "size": "1024x1024",
                "style": "realistic"
            }
        }
