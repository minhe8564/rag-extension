"""
Redis Stream 연동 서비스.

커스텀 히스토리에 기록되는 AI 메시지 메타데이터 중
토큰/지연 관련 정보를 Redis Stream에 적재한다.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Optional

from loguru import logger

from app.core.settings import settings

if TYPE_CHECKING:
    from redis import Redis


class HistoryStreamService:
    """커스텀 히스토리 메타데이터를 Redis Stream으로 내보내는 서비스."""

    def __init__(self) -> None:
        self._redis_client: Optional["Redis"] = None
        self.stream_key: str = "generation:history:metrics"
        self.max_length: int = 10_000  # Stream 길이 제한 (approximate)
        self.redis_db: int = 8

    def _get_client(self) -> "Redis":
        """Redis 동기 클라이언트 생성/재사용."""
        if self._redis_client is None:
            try:
                import redis  # type: ignore import-not-found

                self._redis_client = redis.Redis(
                    host=settings.redis_host,
                    port=settings.redis_port,
                    password=settings.redis_password,
                    username=settings.redis_username,
                    db=self.redis_db,
                    decode_responses=True,
                )
            except Exception as error:  # pragma: no cover - 초기화 실패 로그
                logger.error(f"Failed to initialize Redis client for history stream: {error}")
                raise
        return self._redis_client

    def append_ai_metrics(
        self,
        *,
        user_id: Optional[str],
        session_id: Optional[str],
        llm_no: Optional[Any],
        input_tokens: Optional[Any],
        output_tokens: Optional[Any],
        total_tokens: Optional[Any],
        response_time_ms: Optional[Any],
    ) -> None:
        """AI 응답 메타데이터를 Redis Stream에 기록한다."""
        try:
            client = self._get_client()
        except Exception:
            # 초기화 실패 시 이미 로그 남김. 저장 없이 종료.
            return

        # Redis는 문자열/바이트만 지원하므로 str로 변환하고 None은 제거한다.
        payload: Dict[str, str] = {}

        def _put(key: str, value: Optional[Any]) -> None:
            if value is not None:
                try:
                    payload[key] = str(value)
                except Exception:
                    payload[key] = repr(value)

        _put("user_id", user_id)
        _put("session_id", session_id)
        _put("llm_no", llm_no)
        _put("input_tokens", input_tokens)
        _put("output_tokens", output_tokens)
        _put("total_tokens", total_tokens)
        _put("response_time_ms", response_time_ms)

        if not payload:
            logger.debug("Skip Redis stream write: empty payload")
            return

        try:
            client.xadd(
                self.stream_key,
                payload,
                maxlen=self.max_length,
                approximate=True,
            )
            logger.debug(
                "Appended history metrics to Redis stream",
                payload=payload,
                stream=self.stream_key,
                redis_db=self.redis_db,
            )
        except Exception as error:
            logger.warning(f"Failed to append history metrics to Redis stream: {error}")


_history_stream_service: Optional[HistoryStreamService] = None


def get_history_stream_service() -> HistoryStreamService:
    """HistoryStreamService 싱글톤 인스턴스 반환."""
    global _history_stream_service
    if _history_stream_service is None:
        _history_stream_service = HistoryStreamService()
    return _history_stream_service

