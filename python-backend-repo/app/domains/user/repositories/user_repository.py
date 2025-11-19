"""
USER 테이블 조회 Repository
"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..models.user import User


class UserRepository:
    @staticmethod
    async def find_by_user_no(
        db: AsyncSession,
        user_no: bytes
    ) -> Optional[User]:
        result = await db.execute(
            select(User).where(User.user_no == user_no)
        )
        return result.scalar_one_or_none()
