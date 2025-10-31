"""Endpoints demonstrating role-based access using the `x-user-role` header."""

from fastapi import APIRouter, Depends, Header, HTTPException, status


router = APIRouter(prefix="/access", tags=["Access"])


class RoleChecker:
    """FastAPI dependency that validates the custom `x-user-role` header."""

    def __init__(self, *allowed_roles: str, allow_anonymous: bool = False) -> None:
        self.allowed_roles = allowed_roles
        self.allow_anonymous = allow_anonymous

    async def __call__(
        self,
        x_user_role: str | None = Header(
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


@router.get("/user")
async def user_resource(role: str = Depends(RoleChecker("USER"))):
    """USER 역할만 접근 가능한 엔드포인트."""
    return {
        "resource": "USER",
        "message": "USER 전용 리소스에 접근했습니다.",
        "role": role,
    }


@router.get("/admin")
async def admin_resource(_: str = Depends(RoleChecker("ADMIN"))):
    """ADMIN 역할만 접근 가능한 엔드포인트."""
    return {"resource": "admin", "message": "ADMIN 전용 리소스에 접근했습니다."}


@router.get("/guest", tags=["Access"])
async def guest_resource(role: str = Depends(RoleChecker("USER", "ADMIN", allow_anonymous=True))):
    """헤더가 없으면 ANONYMOUS 로 접근되는 공개 샘플 엔드포인트."""
    return {
        "resource": "guest",
        "message": "익명 접근이 허용된 리소스입니다.",
        "role": role,
    }

