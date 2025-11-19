"""
User authentication models
"""
from dataclasses import dataclass
from typing import Optional
from uuid import UUID


@dataclass
class UserInfo:
    """JWT 토큰에서 추출한 사용자 정보"""
    user_uuid: UUID
    role: str
    is_authenticated: bool = True

