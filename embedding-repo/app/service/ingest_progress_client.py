from __future__ import annotations

import os
import time
from typing import Optional

import httpx
from loguru import logger


class IngestProgressClient:
    """Async progress pusher for EMBEDDING and VECTOR_STORE steps.

    - Uses async httpx.AsyncClient for async embedding loops.
    - Throttles by percentage delta and minimum interval.
    - Defaults runId to fileNo when not provided.
    """

    def __init__(
        self,
        *,
        user_id: Optional[str],
        file_no: Optional[str],
        run_id: Optional[str] = None,
    ) -> None:
        self.user_id = user_id or ""
        self.file_no = file_no or ""
        self.run_id =None

        self.endpoint = os.getenv(
            "PROGRESS_ENDPOINT",
            "http://hebees-rag-orchestrator:8000/ingest/progress",
        )
        try:
            self.min_pct_step = float(os.getenv("PROGRESS_MIN_PERCENT_STEP", "1.0"))
        except Exception:
            self.min_pct_step = 1.0
        try:
            self.min_interval_ms = int(os.getenv("PROGRESS_MIN_INTERVAL_MS", "1500"))
        except Exception:
            self.min_interval_ms = 1500

        self._last_sent_pct: dict[str, Optional[float]] = {}
        self._last_sent_ts: dict[str, int] = {}
        self._last_processed: dict[str, Optional[int]] = {}
        self._last_total: dict[str, Optional[int]] = {}

    def _now_ms(self) -> int:
        return int(time.time() * 1000)

    def _calc_pct(self, processed: Optional[int], total: Optional[int]) -> Optional[float]:
        try:
            if processed is None or total is None or total <= 0:
                return None
            pct = max(0.0, min(100.0, 100.0 * (float(processed) / float(total))))
            return pct
        except Exception:
            return None

    def _should_send(self, step: str, pct: Optional[float], now_ms: int) -> bool:
        if pct is None:
            # No pct info -> allow by time gate
            last_ts = self._last_sent_ts.get(step, 0)
            return (now_ms - last_ts) >= self.min_interval_ms
        
        last_pct = self._last_sent_pct.get(step)
        if last_pct is None:
            return True
        
        if abs(pct - last_pct) >= self.min_pct_step:
            return True
        
        last_ts = self._last_sent_ts.get(step, 0)
        return (now_ms - last_ts) >= self.min_interval_ms

    async def _send(
        self,
        *,
        step: str,
        status: str,
        processed: Optional[int],
        total: Optional[int],
    ) -> None:
        now_ms = self._now_ms()
        pct = self._calc_pct(processed, total)
        
        if status == "RUNNING" and not self._should_send(step, pct, now_ms):
            return

        body = {
            "runId": self.run_id,
            "userId": self.user_id,
            "fileNo": self.file_no,
            "currentStep": step,
            "status": status,
            "processed": int(processed) if processed is not None else 0,
            "total": int(total) if total is not None else 0,
            "ts": now_ms,
        }

        headers = {}
        if self.user_id:
            headers["x-user-uuid"] = self.user_id

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(self.endpoint, json=body, headers=headers)
        except Exception as e:
            # Non-fatal: log and continue
            logger.debug(f"Progress push failed (ignored): {e}")
        finally:
            self._last_sent_ts[step] = now_ms
            if pct is not None:
                self._last_sent_pct[step] = pct
            # Track last seen values
            self._last_processed[step] = processed if processed is not None else self._last_processed.get(step)
            self._last_total[step] = total if total is not None else self._last_total.get(step)

    # Public API for EMBEDDING step
    async def embedding_start(self, total: Optional[int] = None) -> None:
        await self._send(step="EMBEDDING", status="RUNNING", processed=0, total=total)

    async def embedding_advance(self, processed: int, total: Optional[int] = None) -> None:
        await self._send(step="EMBEDDING", status="RUNNING", processed=processed, total=total)

    async def embedding_complete(self, processed: Optional[int] = None, total: Optional[int] = None) -> None:
        processed = processed if processed is not None else self._last_processed.get("EMBEDDING")
        total = total if total is not None else self._last_total.get("EMBEDDING")
        if processed is None and total is not None:
            processed = total
        await self._send(step="EMBEDDING", status="COMPLETED", processed=processed, total=total)

    async def embedding_fail(self, processed: Optional[int] = None, total: Optional[int] = None) -> None:
        processed = processed if processed is not None else self._last_processed.get("EMBEDDING")
        total = total if total is not None else self._last_total.get("EMBEDDING")
        await self._send(step="EMBEDDING", status="FAILED", processed=processed, total=total)

    # Public API for VECTOR_STORE step
    async def vector_store_start(self, total: Optional[int] = None) -> None:
        await self._send(step="VECTOR_STORE", status="RUNNING", processed=0, total=total)

    async def vector_store_advance(self, processed: int, total: Optional[int] = None) -> None:
        await self._send(step="VECTOR_STORE", status="RUNNING", processed=processed, total=total)

    async def vector_store_complete(self, processed: Optional[int] = None, total: Optional[int] = None) -> None:
        processed = processed if processed is not None else self._last_processed.get("VECTOR_STORE")
        total = total if total is not None else self._last_total.get("VECTOR_STORE")
        if processed is None and total is not None:
            processed = total
        await self._send(step="VECTOR_STORE", status="COMPLETED", processed=processed, total=total)

    async def vector_store_fail(self, processed: Optional[int] = None, total: Optional[int] = None) -> None:
        processed = processed if processed is not None else self._last_processed.get("VECTOR_STORE")
        total = total if total is not None else self._last_total.get("VECTOR_STORE")
        await self._send(step="VECTOR_STORE", status="FAILED", processed=processed, total=total)

