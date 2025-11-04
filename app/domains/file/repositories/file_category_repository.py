"""
FILE_CATEGORY 테이블 조회 Repository
"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..models.file_category import FileCategory


class FileCategoryRepository:
    """
    FILE_CATEGORY 테이블 조회 로직을 캡슐화
    """
    
    @staticmethod
    async def find_by_name(
        db: AsyncSession,
        name: str
    ) -> Optional[FileCategory]:
        result = await db.execute(
            select(FileCategory).where(FileCategory.name == name)
        )
        return result.scalar_one_or_none()

