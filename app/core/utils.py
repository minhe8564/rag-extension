"""
Utility functions
"""
import jwt
from fastapi import FastAPI, HTTPException, status
from fastapi.openapi.utils import get_openapi
from typing import Optional, Dict, Any
import logging

from .settings import settings

logger = logging.getLogger(__name__)


def custom_openapi(app: FastAPI):
    """
    Custom OpenAPI schema generator with JWT security
    """
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # JWT 보안 스키마 추가
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT 토큰을 입력하세요. 예: Bearer eyJhbGciOiJIUzUxMiJ9..."
        }
    }
    
    # 보안 요구사항 추가
    openapi_schema["security"] = [{"BearerAuth": []}]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


def extract_token_from_header(authorization: Optional[str]) -> Optional[str]:
    """
    Authorization 헤더에서 JWT 토큰 추출
    
    Args:
        authorization: Authorization 헤더 값
        
    Returns:
        추출된 토큰 문자열, 없으면 None
    """
    if not authorization:
        return None
    
    if authorization.startswith("Bearer "):
        return authorization[7:]
    
    return None


def verify_jwt_token(token: str) -> Dict[str, Any]:
    """
    JWT 토큰 검증 및 디코딩
    
    Args:
        token: JWT 토큰 문자열
        
    Returns:
        디코딩된 토큰 payload (dict)
        
    Raises:
        HTTPException: 토큰 검증 실패 시
            - 401: 토큰 만료, 무효, 또는 검증 실패
    """
    try:
        # JWT 토큰 디코딩 및 검증
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=settings.jwt_supported_algorithms,
            options={
                "verify_signature": True,
                "verify_exp": True,
                "verify_iat": True,
            }
        )
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("JWT token expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid JWT token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    except Exception as e:
        logger.error(f"JWT verification error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token verification failed"
        )

