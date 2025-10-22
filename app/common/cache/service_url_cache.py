"""
서비스 URL 캐시 관리자
"""
import asyncio
import logging
from typing import Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ...database import get_db
from ...admin.models import BaseURL

logger = logging.getLogger(__name__)

class ServiceURLCache:
    """서비스 URL 캐시 관리자"""
    
    def __init__(self):
        self._cache: Dict[str, str] = {}
        self._lock = asyncio.Lock()
        self._initialized = False
    
    async def get_service_url(self, service_name: str) -> Optional[str]:
        """서비스 URL 조회 (캐시 우선)"""
        if not self._initialized:
            await self._initialize_cache()
        
        return self._cache.get(service_name)
    
    async def _initialize_cache(self):
        """캐시 초기화"""
        async with self._lock:
            if self._initialized:
                return
            
            try:
                # DB 연결을 위한 새로운 세션 생성
                from ...database import engine
                from sqlalchemy.ext.asyncio import AsyncSession
                
                async with AsyncSession(engine) as db:
                    result = await db.execute(select(BaseURL))
                    base_urls = result.scalars().all()
                    
                    self._cache = {
                        base_url.service_name: base_url.base_url 
                        for base_url in base_urls
                    }
                    
                    self._initialized = True
                    logger.info(f"Service URL cache initialized with {len(self._cache)} services")
                
            except Exception as e:
                logger.error(f"Failed to initialize service URL cache: {e}")
                raise
    
    async def refresh_cache(self):
        """캐시 갱신"""
        async with self._lock:
            try:
                # DB 연결을 위한 새로운 세션 생성
                from ...database import engine
                from sqlalchemy.ext.asyncio import AsyncSession
                
                async with AsyncSession(engine) as db:
                    result = await db.execute(select(BaseURL))
                    base_urls = result.scalars().all()
                    
                    self._cache = {
                        base_url.service_name: base_url.base_url 
                        for base_url in base_urls
                    }
                    
                    logger.info(f"Service URL cache refreshed with {len(self._cache)} services")
                
            except Exception as e:
                logger.error(f"Failed to refresh service URL cache: {e}")
                raise
    
    def get_cached_url(self, service_name: str) -> Optional[str]:
        """캐시에서 직접 조회 (동기)"""
        return self._cache.get(service_name)

# 전역 캐시 인스턴스
service_url_cache = ServiceURLCache()
