from __future__ import annotations

from typing import Optional

from redis.asyncio import Redis

from app.core.settings import settings


_client: Optional[Redis] = None


def get_redis_client() -> Redis:
    global _client
    if _client is None:
        redis_url = getattr(settings, "redis_url", None)

        host = getattr(settings, "redis_host", None)
        port = getattr(settings, "redis_port", None)
        username = getattr(settings, "redis_username", "default")
        password = getattr(settings, "redis_password", None)

        if not host or not port:
            raise RuntimeError("Redis settings are not configured (host/port)")

        auth_part = ""
        if username and password:
            auth_part = f"{username}:{password}@"
        elif password:
            auth_part = f":{password}@"
        elif username:
            # Treat provided username as password when password is absent (common misnaming)
            auth_part = f":{username}@"

        redis_url = f"redis://{auth_part}{host}:{port}"

        _client = Redis.from_url(
            redis_url, decode_responses=True, db=getattr(settings, "redis_db", 1)
        )
    return _client


async def close_redis_client() -> None:
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None
