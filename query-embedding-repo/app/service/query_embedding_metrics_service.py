"""
Query Embedding 단계 응답시간 메트릭 수집 서비스
Redis DB 4에 메트릭 데이터 저장
"""
import json
import time
from typing import Optional
from redis.asyncio import Redis
from app.core.settings import settings
from loguru import logger


class QueryEmbeddingMetricsService:
    """Query Embedding 단계 메트릭 수집 서비스"""

    def __init__(self):
        self.redis_client: Optional[Redis] = None
        self.metrics_key: str = "query_embedding:metrics:response_time"
        self.ttl_seconds = 86400  # 1일 (기존: 300 = 5분)
        self.metrics_redis_db = 4  # DB 4 사용

    async def _get_redis_client(self) -> Redis:
        """Redis 클라이언트 가져오기 (DB 4 사용)"""
        if self.redis_client is None:
            import redis.asyncio as redis
            self.redis_client = redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                password=settings.redis_password,
                username=settings.redis_username,
                db=self.metrics_redis_db,  # DB 4 사용
                decode_responses=True
            )
        return self.redis_client

    async def record_query_embedding_time(self, time_ms: float, strategy: str = None):
        """
        Query Embedding 응답시간 기록
        
        Args:
            time_ms: 응답시간 (밀리초)
            strategy: 사용된 전략 (선택사항)
        """
        try:
            redis = await self._get_redis_client()
            timestamp = time.time()

            # 메트릭 데이터
            metric_data = {
                "timestamp": timestamp,
                "time_ms": time_ms,
                "strategy": strategy
            }

            # Sorted Set에 추가 (score = timestamp, value = JSON)
            await redis.zadd(
                self.metrics_key,
                {json.dumps(metric_data): timestamp}
            )

            # TTL 설정 (이미 TTL이 있으면 갱신하지 않음)
            ttl = await redis.ttl(self.metrics_key)
            if ttl == -1:
                await redis.expire(self.metrics_key, self.ttl_seconds)

            # 오래된 데이터 자동 정리 (1일 이전 데이터 삭제)
            cutoff_time = timestamp - self.ttl_seconds
            await redis.zremrangebyscore(self.metrics_key, 0, cutoff_time)
            
            logger.debug(f"Recorded query embedding time: {time_ms:.2f}ms (strategy: {strategy})")
        except Exception as e:
            logger.error(f"Failed to record query embedding time: {str(e)}", exc_info=True)


# 싱글톤 인스턴스
_metrics_service: Optional[QueryEmbeddingMetricsService] = None


def get_query_embedding_metrics_service() -> QueryEmbeddingMetricsService:
    """Query Embedding 메트릭 서비스 싱글톤 인스턴스 반환"""
    global _metrics_service
    if _metrics_service is None:
        _metrics_service = QueryEmbeddingMetricsService()
    return _metrics_service
