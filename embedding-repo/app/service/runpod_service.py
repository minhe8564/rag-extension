"""
RUNPOD 서비스
DB에서 RUNPOD 정보를 조회하는 서비스
"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.runpod import Runpod
from loguru import logger


class RunpodService:
    @staticmethod
    async def get_address_by_name(
        db: AsyncSession,
        name: str
    ) -> Optional[str]:
        """
        RUNPOD 이름으로 주소 조회
        
        Args:
            db: 데이터베이스 세션
            name: RUNPOD 이름 (예: "EMBEDDING")
        
        Returns:
            RUNPOD 주소 또는 None
        """
        try:
            result = await db.execute(
                select(Runpod.ADDRESS).where(Runpod.NAME == name)
            )
            address = result.scalar_one_or_none()
            if address:
                logger.info(f"RUNPOD 주소 조회 성공: name={name}, address={address}")
            else:
                logger.warning(f"RUNPOD를 찾을 수 없습니다: name={name}")
            return address
        except Exception as e:
            logger.error(f"RUNPOD 주소 조회 실패: {e}", exc_info=True)
            return None

