"""
JWT 인증 관련 데이터 모델
"""
from pydantic import BaseModel
from typing import Optional
from enum import Enum

class UserRole(str, Enum):
    """사용자 역할"""
    ADMIN = "ADMIN"
    OPTICAL_SHOP = "OPTICAL_SHOP"
    PARTNER = "PARTNER"
    MANUFACTURER = "MANUFACTURER"

class TokenData(BaseModel):
    """JWT 토큰 데이터"""
    user_uuid: str
    role: Optional[UserRole] = None

class UserInfo(BaseModel):
    """사용자 정보"""
    user_uuid: str
    role: UserRole
    is_authenticated: bool = True

class AuthError(BaseModel):
    """인증 에러 응답"""
    error: str
    message: str
    status_code: int