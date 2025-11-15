"""
Redis Stream 연동 서비스.

사용자의 질의 요청이 있을 때
토큰/지연 지표와 사용자 질의를
Redis Stream에 기록한다.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Optional

from loguru import logger

from app.core.settings import settings

if TYPE_CHECKING:
    from redis import Redis


class HistoryStreamService:
    """히스토리에서 필요한 데이터를 Redis Stream으로 내보내는 서비스."""

    def __init__(self) -> None:
        self._redis_client: Optional["Redis"] = None
        self.chatbot_stream_key: str = "generation:history:metrics" # 챗봇 메타데이터 스트림
        self.query_stream_key: str = "generation:history:queries" # 사용자 질의 스트림
        self.error_stream_key: str = "generation:history:errors"  # 에러 이벤트 스트림
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

    def _append_to_stream(self, *, stream_key: str, payload: Dict[str, str], context: str) -> None:
        """공통 Redis Stream 추가 로직."""
        if not payload:
            logger.debug(f"Skip Redis stream write: empty payload ({context})")
            return

        try:
            client = self._get_client()
        except Exception:
            # 초기화 실패 시 이미 로그 남김. 저장 없이 종료.
            return

        try:
            client.xadd(
                stream_key,
                payload,
                maxlen=self.max_length,
                approximate=True,
            )
            logger.debug(
                f"Appended {context} to Redis stream",
                payload=payload,
                stream=stream_key,
                redis_db=self.redis_db,
            )
        except Exception as error:
            logger.warning(f"Failed to append {context} to Redis stream: {error}")

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

        self._append_to_stream(stream_key=self.chatbot_stream_key, payload=payload, context="history metrics")

    def append_user_query(
        self,
        *,
        query: Optional[str],
        user_id: Optional[str],
        session_id: Optional[str],
        strategy: Optional[str],
    ) -> None:
        """사용자 질의를 Redis Stream에 기록한다."""
        payload: Dict[str, str] = {}

        def _put(key: str, value: Optional[Any]) -> None:
            if value is not None:
                try:
                    payload[key] = str(value)
                except Exception:
                    payload[key] = repr(value)

        _put("query", query)
        _put("user_id", user_id)
        _put("session_id", session_id)
        _put("llm", strategy)

        # query 값이 없으면 기록할 필요가 없다.
        if "query" not in payload or not payload["query"].strip():
            logger.debug("Skip Redis stream write: missing query")
            return

        self._append_to_stream(stream_key=self.query_stream_key, payload=payload, context="user query")

    def append_error_event(
        self,
        *,
        error_code: str,
        message: Optional[str],
        error_type: Optional[str],
        user_id: Optional[str],
        session_id: Optional[str],
        llm_no: Optional[Any],
        query: Optional[str] = None,
    ) -> None:
        """에러 이벤트를 별도 Redis Stream에 기록한다."""
        payload: Dict[str, str] = {}

        def _put(key: str, value: Optional[Any]) -> None:
            if value is not None:
                try:
                    payload[key] = str(value)
                except Exception:
                    payload[key] = repr(value)

        _put("error_code", error_code)
        _put("type", error_type)
        _put("message", message)
        _put("user_id", user_id)
        _put("session_id", session_id)
        _put("llm_no", llm_no)
        _put("query", query)

        if not payload:
            logger.debug("Skip Redis error stream write: empty payload")
            return

        self._append_to_stream(stream_key=self.error_stream_key, payload=payload, context="error event")


_history_stream_service: Optional[HistoryStreamService] = None


def get_history_stream_service() -> HistoryStreamService:
    """HistoryStreamService 싱글톤 인스턴스 반환."""
    global _history_stream_service
    if _history_stream_service is None:
        _history_stream_service = HistoryStreamService()
    return _history_stream_service

