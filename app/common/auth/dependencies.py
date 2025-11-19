"""
JWT 인증 의존성 (리팩토링된 버전)
"""
from fastapi import Depends, HTTPException, status, Request
from typing import List, Optional, Union
from .models import UserInfo, UserRole

def get_current_user(request: Request) -> UserInfo:
    """현재 인증된 사용자 정보 반환"""
    user = getattr(request.state, 'user', None)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    return user

def get_current_user_uuid(request: Request) -> str:
    """현재 사용자의 UUID 반환"""
    user = get_current_user(request)
    return user.user_uuid

def get_current_user_role(request: Request) -> UserRole:
    """현재 사용자의 역할 반환"""
    user = get_current_user(request)
    return user.role

class PermissionChecker:
    """권한 체크 클래스"""
    
    def __init__(self, required_roles: List[UserRole], error_message: str):
        self.required_roles = required_roles
        self.error_message = error_message
    
    def __call__(self, request: Request) -> UserInfo:
        user = get_current_user(request)
        
        # ADMIN은 모든 권한을 가짐
        if user.role == UserRole.ADMIN:
            return user
        
        # 요구되는 역할 중 하나라도 있으면 허용
        if user.role in self.required_roles:
            return user
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=self.error_message
        )

def require_roles(required_roles: List[UserRole], error_message: str = "Access denied"):
    """역할 기반 권한 체크 팩토리 함수"""
    return PermissionChecker(required_roles, error_message)

# 기존 함수들을 새로운 구조로 리팩토링
def require_admin(request: Request) -> UserInfo:
    """관리자 권한 필요"""
    return require_roles([], "Admin access required")(request)

def require_optical_shop(request: Request) -> UserInfo:
    """안경점 권한 필요 (관리자 + 안경점)"""
    return require_roles([UserRole.OPTICAL_SHOP], "Optical shop access required")(request)

def require_partner(request: Request) -> UserInfo:
    """협력사 권한 필요 (관리자 + 협력사)"""
    return require_roles([UserRole.PARTNER], "Partner access required")(request)

def require_manufacturer(request: Request) -> UserInfo:
    """제조사 권한 필요 (관리자 + 제조사)"""
    return require_roles([UserRole.MANUFACTURER], "Manufacturer access required")(request)

# 새로운 유연한 권한 체크 함수들
def require_optical_shop_or_partner(request: Request) -> UserInfo:
    """안경점 또는 협력사 권한 필요"""
    return require_roles(
        [UserRole.OPTICAL_SHOP, UserRole.PARTNER], 
        "Optical shop or partner access required"
    )(request)

def require_any_role(request: Request) -> UserInfo:
    """모든 인증된 사용자 허용"""
    return get_current_user(request)