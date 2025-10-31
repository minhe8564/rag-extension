"""
JWT Authentication Middleware
"""
from fastapi import Request, HTTPException, status
import logging
from uuid import UUID

from ...core.utils import extract_token_from_header, verify_jwt_token
from .models import UserInfo

logger = logging.getLogger(__name__)

async def jwt_auth_middleware(request: Request, call_next):
    """
    JWT 인증 미들웨어
    
    요청에 JWT 토큰이 포함되어 있다면 검증 후 사용자 정보를 저장하고,
    토큰이 없다면 그대로 통과시킵니다.
    """
    authorization = request.headers.get("Authorization")
    token = extract_token_from_header(authorization) if authorization else None

    if token:
        try:
            payload = verify_jwt_token(token)

            user_uuid = payload.get("sub")
            role = payload.get("role")

            if not user_uuid or not role:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="유효하지 않은 토큰 페이로드입니다."
                )

            try:
                request.state.user = UserInfo(
                    user_uuid=UUID(str(user_uuid)),
                    role=str(role),
                    is_authenticated=True
                )
            except (ValueError, TypeError):
                logger.warning(f"토큰의 UUID 형식이 올바르지 않습니다: {user_uuid}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="유효하지 않은 토큰 페이로드: 사용자 UUID 형식이 올바르지 않습니다."
                )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"JWT 미들웨어에서 예상치 못한 오류가 발생했습니다: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="서버 내부 오류가 발생했습니다."
            )

    response = await call_next(request)
    return response

