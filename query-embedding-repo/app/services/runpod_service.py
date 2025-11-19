"""
Runpod 서비스 모듈
DB에서 Runpod 주소를 조회하는 기능 제공
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.models.runpod import Runpod
from loguru import logger


class RunpodService:
    """Runpod 주소 조회 서비스"""
    
    @staticmethod
    async def get_address_by_name(runpod_name: str) -> str:
        """
        DB에서 Runpod 이름으로 주소 조회
        
        Args:
            runpod_name: Runpod 이름 (예: "EMBEDDING")
            
        Returns:
            Runpod 주소 (예: "https://xxx-8000.proxy.runpod.net")
            
        Raises:
            ValueError: Runpod을 찾을 수 없거나 주소가 비어있는 경우
        """
        try:
            logger.info(f"[RunpodService] Fetching Runpod address from DB: name={runpod_name}")
            
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(Runpod).where(Runpod.name == runpod_name)
                )
                runpod = result.scalar_one_or_none()
                
                if not runpod:
                    raise ValueError(f"Runpod not found for name: {runpod_name}")
                
                address = runpod.address
                if not address:
                    raise ValueError(f"Runpod address is empty for name: {runpod_name}")
                
                logger.info(f"[RunpodService] Runpod address retrieved: {address}")
                return address.rstrip("/")
                
        except Exception as e:
            logger.error(f"[RunpodService] Error getting Runpod address from DB: {str(e)}")
            raise

