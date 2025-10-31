"""
JWT Authentication Middleware
"""
from fastapi import Request, HTTPException, status
from typing import List
import logging
from uuid import UUID

from ...core.utils import extract_token_from_header, verify_jwt_token
from .models import UserInfo

logger = logging.getLogger(__name__)


# 인증이 필요하지 않은 공개 경로
PUBLIC_PATHS: List[str] = [
    "/",
    "/health",
    "/docs",
    "/openapi.json",
    "/redoc",
    "/rag/health",
]


def is_public_path(path: str) -> bool:
    """경로가 공개 경로인지 확인"""
    return any(path.startswith(public_path) for public_path in PUBLIC_PATHS)


async def jwt_auth_middleware(request: Request, call_next):
    """
    JWT 인증 미들웨어
    
    공개 경로는 인증 없이 통과시키고,
    보호된 경로는 JWT 토큰 검증 후 사용자 정보를 request.state에 저장합니다.
    """
    # 공개 경로는 인증 없이 통과
    if is_public_path(request.url.path):
        return await call_next(request)
    
    # Authorization 헤더에서 토큰 추출
    authorization = request.headers.get("Authorization")
    token = extract_token_from_header(authorization)
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing or invalid",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # JWT 토큰 검증
    try:
        payload = verify_jwt_token(token)
        
        # 사용자 정보 추출
        user_uuid = payload.get("sub")
        role = payload.get("role")
        
        if not user_uuid or not role:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
        
        # request.state에 사용자 정보 저장
        try:
            request.state.user = UserInfo(
                user_uuid=UUID(str(user_uuid)),
                role=str(role),
                is_authenticated=True
            )
        except (ValueError, TypeError) as e:
            logger.warning(f"Invalid UUID format in token: {user_uuid}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload: invalid user UUID format"
            )
        
        # 요청 계속 처리
        response = await call_next(request)
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in JWT middleware: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

