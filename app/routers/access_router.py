"""Endpoints demonstrating role-based access using the `x-user-role` header."""

from fastapi import APIRouter, Depends, Header, HTTPException, status


router = APIRouter(prefix="/access", tags=["Access"])


def require_role(*allowed_roles: str, allow_anonymous: bool = False):
    async def _validate_role(x_user_role: str = Header(None, convert_underscores=False)) -> str:
        if x_user_role is None:
            if allow_anonymous:
                return "ANONYMOUS"
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="x-user-role 헤더가 필요합니다.",
            )

        if x_user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="해당 역할은 이 API를 사용할 수 없습니다.",
            )

        return x_user_role

    return _validate_role


@router.get("/user")
async def user_resource(role: str = Depends(require_role("USER"))):
    """USER 역할만 접근 가능한 엔드포인트."""
    return {
        "resource": "USER",
        "message": "USER 전용 리소스에 접근했습니다.",
        "role": role,
    }


@router.get("/admin")
async def admin_resource(_: str = Depends(require_role("ADMIN"))):
    """ADMIN 역할만 접근 가능한 엔드포인트."""
    return {"resource": "admin", "message": "ADMIN 전용 리소스에 접근했습니다."}


@router.get("/guest", tags=["Access"])
async def guest_resource(role: str = Depends(require_role("USER", "ADMIN", allow_anonymous=True))):
    """헤더가 없으면 ANONYMOUS 로 접근되는 공개 샘플 엔드포인트."""
    return {
        "resource": "guest",
        "message": "익명 접근이 허용된 리소스입니다.",
        "role": role,
    }

