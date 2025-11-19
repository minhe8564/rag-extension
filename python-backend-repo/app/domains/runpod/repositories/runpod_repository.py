"""
RUNPOD 테이블 조회 Repository
"""
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from ..models.runpod import Runpod


class RunpodRepository:
    @staticmethod
    async def find_by_name(
        db: AsyncSession,
        name: str
    ) -> Optional[Runpod]:
        result = await db.execute(
            select(Runpod).where(Runpod.name == name)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def find_all(
        db: AsyncSession
    ) -> List[Runpod]:
        result = await db.execute(
            select(Runpod).order_by(desc(Runpod.created_at))
        )
        return list(result.scalars().all())
    
    @staticmethod
    async def save(
        db: AsyncSession,
        runpod_record: Runpod
    ) -> Runpod:
        db.add(runpod_record)
        await db.commit()
        await db.refresh(runpod_record)
        return runpod_record
    
    @staticmethod
    async def update(
        db: AsyncSession,
        runpod_record: Runpod
    ) -> Runpod:
        await db.commit()
        await db.refresh(runpod_record)
        return runpod_record
    
    @staticmethod
    async def delete(
        db: AsyncSession,
        runpod_record: Runpod
    ) -> bool:
        try:
            await db.delete(runpod_record)
            await db.commit()
            return True
        except Exception as e:
            await db.rollback()
            raise e

