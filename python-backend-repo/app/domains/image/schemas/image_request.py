"""
이미지 생성 요청 DTO
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal

# 허용되는 이미지 크기
ALLOWED_IMAGE_SIZES = [
    "1024x1024",  # 1:1
    "832x1248",   # 2:3
    "1248x832",   # 3:2
    "864x1184",   # 3:4
    "1184x864",   # 4:3
    "896x1152",   # 4:5
    "1152x896",   # 5:4
    "768x1344",   # 9:16
    "1344x768",   # 16:9
    "1536x672",   # 21:9
]

# Literal 타입으로 허용되는 크기 정의
ImageSize = Literal[
    "1024x1024",
    "832x1248",
    "1248x832",
    "864x1184",
    "1184x864",
    "896x1152",
    "1152x896",
    "768x1344",
    "1344x768",
    "1536x672"
]

class ImageGenerateRequest(BaseModel):
    prompt: str = Field(
        ...,
        description="이미지 생성 프롬프트",
        examples=["포근한 크리스마스 분위기의 일러스트, 눈 내리는 마을, 트리와 선물 상자, 따뜻한 조명, 포스터 스타일"]
    )

    size: ImageSize = Field(
        default="1024x1024",
        description="이미지 크기 (허용된 비율만 가능)",
        examples=["1024x1024", "1344x768", "832x1248"]
    )

    style: Optional[str] = Field(
        default=None,
        description="이미지 스타일",
        example="realistic"
    )

    @field_validator("size")
    @classmethod
    def validate_size(cls, v: str) -> str:
        if v not in ALLOWED_IMAGE_SIZES:
            raise ValueError(
                f"허용되지 않은 이미지 크기입니다. "
                f"허용된 크기: {', '.join(ALLOWED_IMAGE_SIZES)}"
            )
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "prompt": "A cute banana with a smiling face",
                "size": "1024x1024",
                "style": "realistic"
            }
        }
