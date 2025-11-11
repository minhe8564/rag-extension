from __future__ import annotations

import logging
import uuid
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clients.minio_client import remove_object
from minio.error import S3Error
from app.core.config.settings import settings
from app.core.clients.milvus_client import delete_by_expr
from app.domains.collection.models.collection import Collection
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
        # remove_object swallows not-found; raises on other S3 errors
        remove_object(file_row.bucket, file_row.path)
    except S3Error as e:
        # Surface storage errors to the client and abort DB deletion
        raise HTTPException(status_code=502, detail=f"MinIO delete failed: {e.code}") from e
    except Exception as e:
        # Unexpected client/runtime error
        raise HTTPException(status_code=500, detail="Storage delete failed") from e

    # Vector (Milvus) cleanup directly (best-effort)
    try:
        # Resolve Milvus target by business rules
        milvus_collection_name: Optional[str] = None
        partition_name: Optional[str] = None

        special_partitions = {"hebees", "public"}
        coll_name: Optional[str] = None
        if getattr(file_row, "collection_no", None):
            try:
                coll = await session.get(Collection, file_row.collection_no)
                coll_name = getattr(coll, "name", None) if coll else None
            except Exception:
                coll_name = None

        if coll_name in special_partitions:
            milvus_collection_name = "publicRetina_1"
            partition_name = coll_name  # 'hebees' or 'public'
        else:
            # Offer-based dedicated collection, e.g., h{offer_no}_1
            offer = getattr(file_row, "offer_no", None) or ""
            if offer:
                milvus_collection_name = f"h{offer}_1"

        if milvus_collection_name:
            file_no_str = _uuid_bytes_to_str(file_row.file_no)
            pk_field = getattr(settings, "milvus_pk_field", "file_no") or "file_no"
            path_field = getattr(settings, "milvus_path_field", "path") or "path"

            # Delete by file_no first
            expr1 = f"{pk_field} == '{file_no_str}'"
            delete_by_expr(milvus_collection_name, expr1, partition_name=partition_name)
            
        else:
            logger.info("Milvus target could not be resolved; skipping vector deletion")
    except Exception as e:
        logger.warning("Vector cleanup (Milvus) failed for file %s: %s", _uuid_bytes_to_str(file_row.file_no), e)

    # Remove DB row
    await session.delete(file_row)
    await session.flush()
