from __future__ import annotations

from typing import Optional, Dict, Any
from datetime import datetime, timezone
from loguru import logger
from fastapi import HTTPException

from app.core.redis_client import get_redis_client
from app.core.settings import settings
from app.schemas.request.ingestProgressEvent import IngestProgressEvent


# Progress aggregation config (weights sum to 1.0)
# CHUNKING is excluded from overall calculation
STEP_ORDER = ["UPLOAD", "EXTRACTION" , "EMBEDDING", "VECTOR_STORE"]
STEP_WEIGHTS = {
    "UPLOAD": 0.20,     
    "EXTRACTION": 0.30,  
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


RUN_META_SCAN_BATCH = 200


def _normalize_file_no(file_no: Optional[str]) -> Optional[str]:
    if not file_no:
        return None
    cleaned = file_no.replace("-", "").strip().lower()
    if len(cleaned) != 32:
        return None
    try:
        bytes.fromhex(cleaned)
    except ValueError:
        return None
    return cleaned


async def _resolve_run_id_for_file(redis, normalized_file_no: str, raw_file_no: Optional[str] = None) -> Optional[str]:
    if not normalized_file_no:
        return None
    latest_key_candidates: list[str] = []
    seen_keys = set()

    def _add_latest_candidate(number: Optional[str]) -> None:
        if not number:
            return
        key = f"ingest:file:{number}:latest_run_id"
        if key in seen_keys:
            return
        seen_keys.add(key)
        latest_key_candidates.append(key)

    _add_latest_candidate(normalized_file_no)
    if raw_file_no:
        clean_raw = raw_file_no.strip()
        lower_raw = clean_raw.lower()
        _add_latest_candidate(lower_raw)
        _add_latest_candidate(clean_raw)

    # 1) Try new latest runId key(s) (no SCAN needed)
    for latest_key in latest_key_candidates:
        try:
            latest = await redis.get(latest_key)
            if latest:
                return latest
        except Exception:
            logger.debug("Failed to read latest runId key for file %s", latest_key)

    return None


async def _aggregate_from_events(
    redis,
    run_id: str,
    pending_event: Optional[Dict[str, Any]] = None,
) -> dict:
    key = f"ingest:run:{run_id}:events"
    rows = await redis.xrevrange(key, count=STREAM_MAXLEN_PER_RUN)
    if pending_event:
        rows.insert(0, ("pending", pending_event))
    step_state = {s: {"processed": None, "total": None, "status": None, "ts": None} for s in STEP_ORDER}

    for _id, fields in rows:
        # Support multiple producer schemas: prefer new keys, fall back to legacy
        step_key = None
        status_key = None
        processed_key = None
        total_key = None
        ts_key = None

        if isinstance(fields, dict):
            # Step: prefer 'currentStep', fallback to 'step'
            step_key = "currentStep" if "currentStep" in fields else ("step" if "step" in fields else None)
            # Status stays consistent but guard anyway
            status_key = "status" if "status" in fields else None
            # Processed/total may vary in presence
            processed_key = "processed" if "processed" in fields else None
            total_key = "total" if "total" in fields else None
            # Timestamp key
            ts_key = "ts" if "ts" in fields else ("timestamp" if "timestamp" in fields else None)

        step = _normalize_step(fields.get(step_key)) if (isinstance(fields, dict) and step_key) else None
        if not step:
            continue
        try:
            processed = int(fields.get(processed_key)) if (processed_key and fields.get(processed_key) is not None) else None
        except Exception:
            processed = None
        try:
            total = int(fields.get(total_key)) if (total_key and fields.get(total_key) is not None) else None
        except Exception:
            total = None
        status = _normalize_status(fields.get(status_key)) if (isinstance(fields, dict) and status_key) else None
        ts = None
        try:
            ts = int(fields.get(ts_key)) if (ts_key and fields.get(ts_key) is not None) else None
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

    # Calculate overall percentage (CHUNKING is excluded as its weight is 0.0)
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
        # Ensure overall_pct is 100.0 when all steps are completed
        overall_pct = 100.0
        # When run is completed, force current_step to the last step
        current_step = STEP_ORDER[-1]
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

            file_no_raw = (ev.fileNo or "").strip()
            normalized_file_no = _normalize_file_no(file_no_raw)
            run_id = (ev.runId or "").strip()
            step = _normalize_step(ev.currentStep)
            status = _normalize_status(ev.status)
            user_id = ev.userId or user_id_header
            event_type = ev.eventType or _infer_event_type(status)
            ts_ms = ev.ts or int(datetime.now(timezone.utc).timestamp() * 1000)

            if not run_id and normalized_file_no:
                run_id = await _resolve_run_id_for_file(redis, normalized_file_no, file_no_raw)

            if not run_id:
                raise HTTPException(
                    status_code=400,
                    detail="runId is required (or provide a fileNo that can be resolved to an existing run)",
                )

            if not step:
                raise HTTPException(status_code=400, detail="currentStep is required and must be valid")

            fields = {
                "eventType": event_type,
                "runId": run_id,
                "userId": user_id or "",
                "fileNo": file_no_raw,
                "currentStep": step,
                "status": status or "",
                "processed": str(ev.processed) if ev.processed is not None else "",
                "total": str(ev.total) if ev.total is not None else "",
                "ts": str(ts_ms),
            }

            per_run_key = f"ingest:run:{run_id}:events"
            global_key = "ingest:progress"
            agg = await _aggregate_from_events(redis, run_id, pending_event=fields)

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

            # Always use the aggregated overall_pct (don't use max with prev to allow decreases)
            # Ensure COMPLETED status shows 100% overall
            new_overall = 100.0 if agg["run_status"] == "COMPLETED" else agg["overall_pct"]
            delta = (new_overall - (prev_overall or 0.0)) if prev_overall is not None else new_overall
            should_write = (
                abs(delta) >= DEBOUNCE_DELTA_PCT
                or (prev_current_step or "") != (agg["current_step"] or "")
                or (prev_status or "") != (agg["run_status"] or "")
            )

            # Always add overallPct and progressPct to the stream event for SSE
            fields_with_progress = dict(fields)
            fields_with_progress.update(
                {
                    "progressPct": f"{agg['current_step_pct']:.6f}",
                    "overallPct": f"{new_overall:.6f}",
                }
            )
            # Add to per-run stream (with progress fields included)
            await redis.xadd(per_run_key, fields_with_progress, maxlen=STREAM_MAXLEN_PER_RUN, approximate=True)
            # Update the global stream with progress fields
            await redis.xadd(global_key, fields_with_progress, maxlen=STREAM_MAXLEN_GLOBAL, approximate=True)

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
                if file_no_raw:
                    mapping["fileNo"] = file_no_raw
                await redis.hset(meta_key, mapping=mapping)

            if agg["run_status"] in ("COMPLETED", "FAILED"):
                fin_user_id = user_id
                if not fin_user_id:
                    meta = await redis.hgetall(meta_key)
                    fin_user_id = meta.get("userId") if meta else None

                if fin_user_id:
                    await redis.srem(f"ingest:user:{fin_user_id}:runs", run_id)

                # Set expire on completed/failed run data
                ttl_sec = getattr(settings, "ingest_completed_ttl_sec", 0)
                if ttl_sec > 0:
                    # Expire meta hash
                    await redis.expire(meta_key, ttl_sec)
                    # Expire per-run events stream
                    await redis.expire(per_run_key, ttl_sec)
                    # Expire file latest runId key if fileNo exists
                    if file_no_raw:
                        file_latest_key = f"ingest:file:{file_no_raw}:latest_run_id"
                        await redis.expire(file_latest_key, ttl_sec)
                    logger.debug(
                        f"Set expire on completed run - runId={run_id}, ttl={ttl_sec}s, "
                        f"keys=[{meta_key}, {per_run_key}]"
                    )

                run_event_type = "RUN_COMPLETED" if agg["run_status"] == "COMPLETED" else "RUN_FAILED"
                # new_overall is already 100.0 for COMPLETED status (set above)
                run_fields = {
                    "eventType": run_event_type,
                    "runId": run_id,
                    "userId": fin_user_id or "",
                    "fileNo": file_no_raw,
                    "currentStep": agg["current_step"] or step,
                    "status": agg["run_status"],
                    "processed": str(ev.processed) if ev.processed is not None else "",
                    "total": str(ev.total) if ev.total is not None else "",
                    "progressPct": f"{agg['current_step_pct']:.6f}",
                    "overallPct": f"{new_overall:.6f}",
                    "ts": str(ts_ms),
                }
                await redis.xadd(global_key, run_fields, maxlen=STREAM_MAXLEN_GLOBAL, approximate=True)

            return {"status": "OK"}

        except Exception as e:
            logger.exception("Failed to push ingest progress: {}", e)
            raise
