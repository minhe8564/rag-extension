from __future__ import annotations

from typing import Optional, Dict, Any
from datetime import datetime, timezone
from loguru import logger
from fastapi import HTTPException

from app.core.redis_client import get_redis_client
from app.schemas.request.ingestProgressEvent import IngestProgressEvent


# Progress aggregation config (weights sum to 1.0)
STEP_ORDER = ["UPLOAD", "EXTRACTION", "CHUNKING", "EMBEDDING", "VECTOR_STORE"]
STEP_WEIGHTS = {
    "UPLOAD": 0.20,
    "EXTRACTION": 0.20,
    "CHUNKING": 0.10,
    "EMBEDDING": 0.40,
    "VECTOR_STORE": 0.10,
}

# Stream trimming
STREAM_MAXLEN_GLOBAL = 20000
STREAM_MAXLEN_PER_RUN = 500

# Debounce threshold in percentage points
DEBOUNCE_DELTA_PCT = 1.0


def _normalize_step(name: Optional[str]) -> Optional[str]:
    if not name:
        return None
    n = name.strip().upper().replace("-", "_")
    return n if n in STEP_ORDER else None


def _normalize_status(s: Optional[str]) -> Optional[str]:
    if not s:
        return None
    n = s.strip().upper()
    allowed = {"PENDING", "RUNNING", "COMPLETED", "FAILED"}
    return n if n in allowed else None


def _infer_event_type(status: Optional[str]) -> str:
    if status == "COMPLETED":
        return "STEP_END"
    if status == "FAILED":
        return "STEP_END"
    return "STEP_UPDATE"


def _calc_pct(processed: Optional[int], total: Optional[int], status: Optional[str]) -> Optional[float]:
    try:
        if total and total > 0 and processed is not None:
            pct = max(0.0, min(100.0, 100.0 * (float(processed) / float(total))))
            return pct
        if status == "COMPLETED":
            return 100.0
        return 0.0
    except Exception:
        return None


async def _aggregate_from_events(redis, run_id: str) -> dict:
    key = f"ingest:run:{run_id}:events"
    rows = await redis.xrevrange(key, count=STREAM_MAXLEN_PER_RUN)
    step_state = {s: {"processed": None, "total": None, "status": None, "ts": None} for s in STEP_ORDER}

    for _id, fields in rows:
        step = _normalize_step(fields.get("currentStep")) if isinstance(fields, dict) else None
        if not step:
            continue
        try:
            processed = int(fields.get("processed")) if fields.get("processed") is not None else None
        except Exception:
            processed = None
        try:
            total = int(fields.get("total")) if fields.get("total") is not None else None
        except Exception:
            total = None
        status = _normalize_status(fields.get("status")) if isinstance(fields, dict) else None
        ts = None
        try:
            ts = int(fields.get("ts")) if fields.get("ts") is not None else None
        except Exception:
            ts = None

        st = step_state[step]
        if processed is not None:
            st["processed"] = max(st["processed"] or 0, processed)
        if total is not None:
            st["total"] = max(st["total"] or 0, total)
        if status:
            if st["ts"] is None or (ts or 0) >= (st["ts"] or 0):
                st["status"] = status
                st["ts"] = ts

    per_step_pct: dict[str, float] = {}
    completed_any_failed = False
    for step in STEP_ORDER:
        st = step_state[step]
        pct = _calc_pct(st["processed"], st["total"], st["status"]) or 0.0
        per_step_pct[step] = pct
        if st["status"] == "FAILED":
            completed_any_failed = True

    overall = 0.0
    for step in STEP_ORDER:
        overall += STEP_WEIGHTS[step] * (per_step_pct[step] / 100.0)
    overall_pct = max(0.0, min(100.0, overall * 100.0))

    current_step = None
    running_steps = [s for s in STEP_ORDER if step_state[s]["status"] == "RUNNING"]
    if running_steps:
        current_step = running_steps[-1]
    else:
        completed_steps = [s for s in STEP_ORDER if step_state[s]["status"] == "COMPLETED"]
        current_step = completed_steps[-1] if completed_steps else None

    if completed_any_failed:
        run_status = "FAILED"
    elif all(per_step_pct[s] >= 100.0 for s in STEP_ORDER):
        run_status = "COMPLETED"
    elif any(per_step_pct[s] > 0.0 for s in STEP_ORDER):
        run_status = "RUNNING"
    else:
        run_status = "PENDING"

    current_step_pct = per_step_pct.get(current_step, 0.0) if current_step else 0.0

    return {
        "per_step_pct": per_step_pct,
        "overall_pct": overall_pct,
        "current_step": current_step,
        "current_step_pct": current_step_pct,
        "run_status": run_status,
    }


class IngestProgressService:
    async def push_event(self, ev: IngestProgressEvent, user_id_header: Optional[str] = None) -> Dict[str, Any]:
        """Push an event, update streams/meta, and emit terminal events if needed."""
        try:
            redis = get_redis_client()

            run_id = (ev.runId or "").strip()
            step = _normalize_step(ev.currentStep)
            status = _normalize_status(ev.status)
            user_id = ev.userId or user_id_header
            event_type = ev.eventType or _infer_event_type(status)
            ts_ms = ev.ts or int(datetime.now(timezone.utc).timestamp() * 1000)

            if not run_id:
                raise HTTPException(status_code=400, detail="runId is required")
            if not step:
                raise HTTPException(status_code=400, detail="currentStep is required and must be valid")

            fields = {
                "eventType": event_type,
                "runId": run_id,
                "userId": user_id or "",
                "fileNo": ev.fileNo or "",
                "currentStep": step,
                "status": status or "",
                "processed": str(ev.processed) if ev.processed is not None else "",
                "total": str(ev.total) if ev.total is not None else "",
                "ts": str(ts_ms),
            }

            per_run_key = f"ingest:run:{run_id}:events"
            global_key = "ingest:progress"
            await redis.xadd(per_run_key, fields, maxlen=STREAM_MAXLEN_PER_RUN, approximate=True)
            await redis.xadd(global_key, fields, maxlen=STREAM_MAXLEN_GLOBAL, approximate=True)

            agg = await _aggregate_from_events(redis, run_id)

            meta_key = f"ingest:run:{run_id}:meta"
            prev_overall = None
            prev_current_step = None
            prev_status = None
            try:
                prev = await redis.hgetall(meta_key)
                if prev:
                    prev_overall = float(prev.get("overallPct")) if prev.get("overallPct") else None
                    prev_current_step = prev.get("currentStep")
                    prev_status = prev.get("status")
            except Exception:
                prev = {}

            new_overall = max(prev_overall or 0.0, agg["overall_pct"]) if prev_overall is not None else agg["overall_pct"]
            delta = (new_overall - (prev_overall or 0.0)) if prev_overall is not None else new_overall
            should_write = (
                abs(delta) >= DEBOUNCE_DELTA_PCT
                or (prev_current_step or "") != (agg["current_step"] or "")
                or (prev_status or "") != (agg["run_status"] or "")
            )

            if should_write:
                updated_at = datetime.fromtimestamp(ts_ms / 1000.0, tz=timezone.utc).isoformat()
                mapping = {
                    "status": agg["run_status"],
                    "currentStep": agg["current_step"] or step,
                    "progressPct": f"{agg['current_step_pct']:.6f}",
                    "overallPct": f"{new_overall:.6f}",
                    "updatedAt": updated_at,
                }
                if user_id:
                    mapping["userId"] = user_id
                if ev.fileNo:
                    mapping["fileNo"] = ev.fileNo
                await redis.hset(meta_key, mapping=mapping)

                derived_fields = dict(fields)
                derived_fields.update(
                    {
                        "progressPct": f"{agg['current_step_pct']:.6f}",
                        "overallPct": f"{new_overall:.6f}",
                    }
                )
                await redis.xadd(global_key, derived_fields, maxlen=STREAM_MAXLEN_GLOBAL, approximate=True)

            if agg["run_status"] in ("COMPLETED", "FAILED"):
                fin_user_id = user_id
                if not fin_user_id:
                    meta = await redis.hgetall(meta_key)
                    fin_user_id = meta.get("userId") if meta else None

                if fin_user_id:
                    await redis.srem(f"ingest:user:{fin_user_id}:runs", run_id)

                run_event_type = "RUN_COMPLETED" if agg["run_status"] == "COMPLETED" else "RUN_FAILED"
                run_fields = {
                    "eventType": run_event_type,
                    "runId": run_id,
                    "userId": fin_user_id or "",
                    "fileNo": ev.fileNo or "",
                    "currentStep": agg["current_step"] or step,
                    "status": agg["run_status"],
                    "processed": str(ev.processed) if ev.processed is not None else "",
                    "total": str(ev.total) if ev.total is not None else "",
                    "progressPct": f"{agg['current_step_pct']:.6f}",
                    "overallPct": f"{max(100.0, new_overall) if agg['run_status']=='COMPLETED' else new_overall:.6f}",
                    "ts": str(ts_ms),
                }
                await redis.xadd(global_key, run_fields, maxlen=STREAM_MAXLEN_GLOBAL, approximate=True)

            return {"status": "OK"}

        except Exception as e:
            logger.exception("Failed to push ingest progress: {}", e)
            raise
