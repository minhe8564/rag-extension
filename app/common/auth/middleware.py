"""
JWT 인증 미들웨어
"""
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from typing import Optional
import logging
from .jwt_handler import jwt_handler
from .models import UserInfo, AuthError, UserRole

logger = logging.getLogger(__name__)

class JWTAuthMiddleware:
    """JWT 인증 미들웨어"""
    def __init__(self):
        self.public_paths = {
            "/",
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json"
        }
    
    def is_public_path(self, path: str) -> bool:
        """공개 경로 확인"""
        return (path in self.public_paths or 
                path.startswith("/ai/api/health") or
                # AI 서비스 프록시 경로 (새 서비스 추가 시 자동으로 포함됨)
                (path.startswith("/ai/api/") and not path.startswith("/ai/api/admin/") and not path.startswith("/ai/api/me")))
    
    async def __call__(self, request: Request, call_next):
        """미들웨어 호출"""
        path = request.url.path

        # 공개 경로는 인증 없이 통과
        if self.is_public_path(path):
            return await call_next(request)
        
         # JWT 토큰 추출
        token = self.extract_token(request)

        if not token:
            return self.create_auth_error("Token not provided", status.HTTP_401_UNAUTHORIZED)
        
        # 토큰 검증
        token_data = jwt_handler.verify_token(token)
        if not token_data:
            return self.create_auth_error("Invalid token", status.HTTP_401_UNAUTHORIZED)
        
        # 사용자 정보를 request state에 저장
        user_info = UserInfo(
            user_uuid = token_data.user_uuid,
            role = token_data.role,
            is_authenticated = True
        )

        request.state.user = user_info
        
        logger.info(f"Authenticated user: {user_info.user_uuid} with role: {user_info.role}")
        
        return await call_next(request)

    def extract_token(self, request: Request) -> Optional[str]:
        """요청에서 JWT 토큰 추출"""
        # Authorization 헤더에서 Bearer 토큰 추출
        authorization = request.headers.get("Authorization")
        if authorization:
            return jwt_handler.extract_token_from_header(authorization)
        
        return None

    def create_auth_error(self, message: str, status_code: int) -> JSONResponse:
        """인증 에러 생성"""
        error_response = AuthError(
            error = "Authentication Error",
            message = message,
            status_code = status_code
        )

        return JSONResponse(
            status_code = status_code,
            content = error_response.dict()
        )

jwt_auth_middleware = JWTAuthMiddleware()