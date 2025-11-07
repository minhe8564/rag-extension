from __future__ import annotations

from typing import Optional
import logging

from pymilvus import connections, Collection

from app.core.settings import settings


logger = logging.getLogger(__name__)

_connected: bool = False


def _ensure_connection() -> None:
    global _connected
    if _connected:
        return
    host = getattr(settings, "milvus_host", None) or getattr(settings, "MILVUS_HOST", None) or "localhost"
    port = str(getattr(settings, "milvus_port", None) or getattr(settings, "MILVUS_PORT", None) or "19530")
    connections.connect(alias="default", host=host, port=port)
    _connected = True


def get_collection(name: str) -> Collection:
    _ensure_connection()
    return Collection(name)


def delete_by_expr(collection_name: str, expr: str, *, partition_name: str | None = None) -> int:
    """Delete vectors by boolean expression. Returns number of entities marked deleted.

    Milvus performs soft deletion; compaction may be required to purge.
    """
    try:
        col = get_collection(collection_name)
        if partition_name:
            res = col.delete(expr, partition_name=partition_name)
        else:
            res = col.delete(expr)
        # res typically contains delete count info; format differs by version
        logger.info(
            "Milvus delete: collection=%s partition=%s expr=%s result=%s",
            collection_name,
            partition_name,
            expr,
            res,
        )
        return 1
    except Exception as e:
        logger.warning(
            "Milvus delete failed: collection=%s partition=%s expr=%s error=%s",
            collection_name,
            partition_name,
            expr,
            e,
        )
        return 0
