"""
JWT 토큰 처리 유틸리티 (리팩토링된 버전)
"""
from typing import Optional
import jwt as pyjwt
from .models import TokenData, UserRole
from ...config import settings
import logging

logger = logging.getLogger(__name__)

class JWTHandler:
    """JWT 토큰 처리 클래스 (리팩토링된 버전)"""
    
    def __init__(self):
        self.secret_key = settings.jwt_secret
        self.algorithm = settings.jwt_algorithm
        self.supported_algorithms = settings.jwt_supported_algorithms
    
    def verify_token(self, token: str) -> Optional[TokenData]:
        """토큰 검증 및 데이터 추출"""
        try:
            payload = pyjwt.decode(
                token, 
                self.secret_key, 
                algorithms=self.supported_algorithms
            )
            user_uuid: str = payload.get("sub")
            role: str = payload.get("role")
            
            if user_uuid is None:
                return None
            
            token_data = TokenData(
                user_uuid=user_uuid,
                role=UserRole(role) if role else None
            )
            return token_data
            
        except pyjwt.InvalidTokenError as e:
            logger.warning(f"JWT verification failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during JWT verification: {e}")
            return None
    
    def extract_token_from_header(self, authorization: str) -> Optional[str]:
        """Authorization 헤더에서 토큰 추출"""
        if not authorization:
            return None
        
        try:
            scheme, token = authorization.split()
            if scheme.lower() != "bearer":
                return None
            return token
        except ValueError:
            return None

# 전역 인스턴스
jwt_handler = JWTHandler()