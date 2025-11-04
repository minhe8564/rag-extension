"""
FILE 테이블 조회 Repository
"""
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func

from ..models.file import File


class FileRepository:
    @staticmethod
    async def find_by_file_no(
        db: AsyncSession,
        file_no: bytes
    ) -> Optional[File]:
        result = await db.execute(
            select(File).where(File.file_no == file_no)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def find_by_user_no_and_category(
        db: AsyncSession,
        user_no: bytes,
        file_category_no: bytes,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[File]:
        query = (
            select(File)
            .where(File.user_no == user_no)
            .where(File.file_category_no == file_category_no)
            .order_by(desc(File.created_at))
        )
        
        if limit is not None:
            query = query.limit(limit)
        if offset is not None:
            query = query.offset(offset)
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    async def count_by_user_no_and_category(
        db: AsyncSession,
        user_no: bytes,
        file_category_no: bytes
    ) -> int:
        result = await db.execute(
            select(func.count(File.file_no))
            .where(File.user_no == user_no)
            .where(File.file_category_no == file_category_no)
        )
        return result.scalar_one() or 0
    
    @staticmethod
    async def save(
        db: AsyncSession,
        file_record: File
    ) -> File:
        db.add(file_record)
        await db.commit()
        await db.refresh(file_record)
        return file_record
    
    @staticmethod
    async def delete(
        db: AsyncSession,
        file_record: File
    ) -> bool:
        try:
            await db.delete(file_record)
            await db.commit()
            return True
        except Exception as e:
            await db.rollback()
            raise e

