"""
인증/인가 유틸리티
x-user-role 헤더 검증 및 권한 제어
"""
from fastapi import Header, HTTPException, status
from typing import Optional


class RoleChecker:
    def __init__(self, *allowed_roles: str, allow_anonymous: bool = False) -> None:
        self.allowed_roles = allowed_roles
        self.allow_anonymous = allow_anonymous
    
    async def __call__(
        self,
        x_user_role: Optional[str] = Header(
            default=None,
            alias="x-user-role",
            description="게이트웨이가 전달하는 사용자 역할 헤더 (예: USER, ADMIN)",
        ),
    ) -> str:
        if x_user_role is None:
            if self.allow_anonymous:
                return "ANONYMOUS"
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="x-user-role 헤더가 필요합니다.",
            )
        
        if self.allowed_roles and x_user_role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="해당 역할은 이 API를 사용할 수 없습니다.",
            )
        
        return x_user_role

def check_role(*allowed_roles: str, allow_anonymous: bool = False):
    return RoleChecker(*allowed_roles, allow_anonymous=allow_anonymous)