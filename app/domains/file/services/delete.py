from __future__ import annotations

import logging
import uuid
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clients.minio_client import remove_object
from app.core.config.settings import settings
from app.core.clients.milvus_client import delete_by_expr
from app.domains.file.models.file import File


logger = logging.getLogger(__name__)


def _uuid_bytes_to_str(b: bytes) -> str:
    try:
        return str(uuid.UUID(bytes=b))
    except Exception:
        return b.hex()


async def delete_file_entity(
    session: AsyncSession,
    *,
    file_row: File,
    user_role: Optional[str] = None,
) -> None:
    """Delete a single file: MinIO object -> vector cleanup (optional) -> DB row.

    - Swallows MinIO not-found.
    - Vector cleanup is best-effort (logs on failure).
    - Always removes the DB row in the end.
    """
    # Remove object from MinIO
    try:
        remove_object(file_row.bucket, file_row.path)
    except Exception as e:
        logger.warning("MinIO removal failed for %s/%s: %s", file_row.bucket, file_row.path, e)

    # Vector (Milvus) cleanup directly (best-effort)
    try:
        collection_name = getattr(settings, "milvus_collection", "") or ""
        if collection_name:
            file_no_str = _uuid_bytes_to_str(file_row.file_no)
            pk_field = getattr(settings, "milvus_pk_field", "fileNo") or "fileNo"
            path_field = getattr(settings, "milvus_path_field", "path") or "path"

            # Try delete by fileNo
            expr1 = f"{pk_field} == '{file_no_str}'"
            delete_by_expr(collection_name, expr1)

            # Also attempt by path (covers alternative indexing)
            if file_row.path:
                # Escape single quotes in path for expr
                safe_path = file_row.path.replace("'", "\\'")
                expr2 = f"{path_field} == '{safe_path}'"
                delete_by_expr(collection_name, expr2)
        else:
            logger.info("Milvus collection not configured; skipping vector deletion")
    except Exception as e:
        logger.warning("Vector cleanup (Milvus) failed for file %s: %s", _uuid_bytes_to_str(file_row.file_no), e)

    # Remove DB row
    await session.delete(file_row)
    await session.flush()
