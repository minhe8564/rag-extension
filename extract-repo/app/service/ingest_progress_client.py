from __future__ import annotations

import os
import time
from typing import Optional

import httpx
from loguru import logger


class IngestProgressPusher:
    """Lightweight progress pusher for EXTRACTION step.

    - Uses sync httpx.Client so it can be called from sync extraction loops.
    - Throttles by percentage delta and minimum interval.
    - Defaults runId to fileNo when not provided.
    """

    def __init__(
        self,
        *,
        user_id: Optional[str],
        file_no: Optional[str],
        run_id: Optional[str] = None,
        step_name: str = "EXTRACTION",
    ) -> None:
        self.user_id = user_id or ""
        self.file_no = file_no or ""
        self.run_id = None
        self.step_name = step_name

        self.endpoint = os.getenv(
            "PROGRESS_ENDPOINT",
            "http://hebees-rag-orchestrator:8000/ingest/progress",
        )
        try:
            self.min_pct_step = float(os.getenv("PROGRESS_MIN_PERCENT_STEP", "2.0"))
        except Exception:
            self.min_pct_step = 2.0
        try:
            self.min_interval_ms = int(os.getenv("PROGRESS_MIN_INTERVAL_MS", "1500"))
        except Exception:
            self.min_interval_ms = 1500

        self._last_sent_pct: Optional[float] = None
        self._last_sent_ts: int = 0
        self._last_processed: Optional[int] = None
        self._last_total: Optional[int] = None

        # Lazy init client per instance
        self._client: Optional[httpx.Client] = None

    def _now_ms(self) -> int:
        return int(time.time() * 1000)

    def _client_get(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(timeout=5.0)
        return self._client

    def _calc_pct(self, processed: Optional[int], total: Optional[int]) -> Optional[float]:
        try:
            if processed is None or total is None or total <= 0:
                return None
            pct = max(0.0, min(100.0, 100.0 * (float(processed) / float(total))))
            return pct
        except Exception:
            return None

    def _should_send(self, pct: Optional[float], now_ms: int) -> bool:
        if pct is None:
            # No pct info -> allow by time gate
            return (now_ms - self._last_sent_ts) >= self.min_interval_ms
        if self._last_sent_pct is None:
            return True
        if abs(pct - self._last_sent_pct) >= self.min_pct_step:
            return True
        return (now_ms - self._last_sent_ts) >= self.min_interval_ms

    def _send(self, *, status: str, processed: Optional[int], total: Optional[int]) -> None:
        now_ms = self._now_ms()
        pct = self._calc_pct(processed, total)
        if status == "RUNNING" and not self._should_send(pct, now_ms):
            logger.debug(f"[PROGRESS] 전송 스킵 (throttling) - status={status}, processed={processed}, total={total}, pct={pct}")
            return

        body = {
            "userId": self.user_id,
            "fileNo": self.file_no,
            "currentStep": self.step_name,
            "status": status,
            "processed": int(processed) if processed is not None else 0,
            "total": int(total) if total is not None else 0,
            "ts": now_ms,
        }
        
        # runId가 None이 아닐 때만 body에 포함
        if self.run_id is not None:
            body["runId"] = self.run_id

        headers = {"x-user-uuid": self.user_id}

        logger.info(f"[PROGRESS] 진행률 전송 시도 - endpoint={self.endpoint}, body={body}, headers={headers}")

        try:
            client = self._client_get()
            response = client.post(self.endpoint, json=body, headers=headers)
            response.raise_for_status()
            logger.info(f"[PROGRESS] 진행률 전송 성공 - status_code={response.status_code}, runId={self.run_id}")
        except Exception as e:
            # Non-fatal: log and continue
            logger.warning(f"[PROGRESS] 진행률 전송 실패 (무시됨) - endpoint={self.endpoint}, error={e}")
        finally:
            self._last_sent_ts = now_ms
            if pct is not None:
                self._last_sent_pct = pct
        # Track last seen values
        self._last_processed = processed if processed is not None else self._last_processed
        self._last_total = total if total is not None else self._last_total

    # Public API
    def start(self, total: Optional[int] = None) -> None:
        self._send(status="RUNNING", processed=0, total=total)

    def advance(self, processed: int, total: Optional[int] = None) -> None:
        # Only RUNNING updates here
        self._send(status="RUNNING", processed=processed, total=total)

    def complete(self, processed: Optional[int] = None, total: Optional[int] = None) -> None:
        # If not provided, try to finalize with last known values
        processed = processed if processed is not None else self._last_processed
        total = total if total is not None else self._last_total
        if processed is None and total is not None:
            processed = total
        self._send(status="COMPLETED", processed=processed, total=total)

    def fail(self, processed: Optional[int] = None, total: Optional[int] = None) -> None:
        processed = processed if processed is not None else self._last_processed
        total = total if total is not None else self._last_total
        self._send(status="FAILED", processed=processed, total=total)

