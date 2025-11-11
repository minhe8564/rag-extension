from __future__ import annotations

from typing import Optional

from redis.asyncio import Redis

from app.core.config.settings import settings


_client: Optional[Redis] = None


def get_redis_client() -> Redis:
    global _client
    if _client is None:
        if not getattr(settings, "redis_url", None):
            raise RuntimeError("Redis settings are not configured (redis_url)")
        _client = Redis.from_url(settings.redis_url, decode_responses=True, db=getattr(settings, "redis_db", 1))
    return _client


async def close_redis_client() -> None:
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None
