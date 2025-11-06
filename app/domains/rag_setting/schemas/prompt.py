"""
프롬프트 관련 스키마 정의
"""
from __future__ import annotations

from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator


class PromptCreateRequest(BaseModel):
    """프롬프트 생성 요청"""
    name: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="프롬프트명"
    )
    type: Literal["system", "user"] = Field(
        ...,
        description="프롬프트 유형 (구분용, DB 저장 안됨)"
    )
    content: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="프롬프트 내용"
    )

    @field_validator('name', 'content')
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        """공백 문자열 검증"""
        if not v or not v.strip():
            raise ValueError('빈 문자열은 허용되지 않습니다.')
        return v.strip()


class PromptCreateResponse(BaseModel):
    """프롬프트 생성 응답"""
    promptNo: str = Field(..., description="생성된 프롬프트 ID (UUID)")

    class Config:
        from_attributes = True


class PromptListItem(BaseModel):
    """프롬프트 목록 아이템"""
    promptNo: str = Field(..., description="프롬프트 ID (UUID)")
    name: str = Field(..., description="프롬프트명")
    type: Literal["system", "user"] = Field(..., description="프롬프트 유형")
    content: str = Field(..., description="프롬프트 내용")

    class Config:
        from_attributes = True


class PaginationInfo(BaseModel):
    """페이지네이션 정보"""
    pageNum: int = Field(..., description="조회할 페이지 번호")
    pageSize: int = Field(..., description="페이지 당 항목 수")
    totalItems: int = Field(..., description="총 항목의 수")
    totalPages: int = Field(..., description="총 페이지의 수")
    hasNext: bool = Field(..., description="다음 페이지의 존재 여부")


class PromptDetailResponse(BaseModel):
    """프롬프트 상세 정보"""
    promptNo: str = Field(..., description="프롬프트 ID (UUID)")
    name: str = Field(..., description="프롬프트명")
    type: Literal["system", "user"] = Field(..., description="프롬프트 유형")
    content: str = Field(..., description="프롬프트 내용")

    class Config:
        from_attributes = True


class PromptUpdateRequest(BaseModel):
    """프롬프트 수정 요청"""
    name: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="프롬프트명"
    )
    content: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="프롬프트 내용"
    )

    @field_validator('name', 'content')
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        """공백 문자열 검증"""
        if not v or not v.strip():
            raise ValueError('빈 문자열은 허용되지 않습니다.')
        return v.strip()
