from __future__ import annotations

from datetime import timedelta
from pathlib import Path
import uuid

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from minio import Minio
from minio.error import S3Error

from app.core.config.settings import settings
from urllib.parse import urlparse
from app.domains.collection.models.collection import Collection
from app.domains.file.repositories.file_repository import FileRepository
from app.core.utils.uuid_utils import _get_offer_no_by_user


def _get_minio_client_for_base(base_url: str) -> Minio:
    parsed = urlparse(base_url)
    return Minio(
        endpoint=parsed.netloc,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        secure=(parsed.scheme == "https"),
        region=settings.minio_region if settings.minio_region else None,
    )


async def get_presigned_url(
    *,
    bucket: str,
    object_name: str,
    content_type: str | None = None,
    days: int = 7,
    version_id: str | None = None,
    inline: bool = True,
) -> str:
    # Clamp expiration to [1, 7]
    days = max(1, min(days, 7))

    disposition = "inline" if inline else "attachment"
    safe_name = Path(object_name).name
    headers: dict[str, str] = {
        "response-content-disposition": f'{disposition}; filename="{safe_name}"',
    }
    if content_type:
        headers["response-content-type"] = content_type

    # Choose signing host: prefer public endpoint to avoid host-rewrite issues
    sign_base = settings.minio_public_endpoint_url or settings.minio_endpoint_url
    client = _get_minio_client_for_base(sign_base)
    try:
        url = client.presigned_get_object(
            bucket_name=bucket,
            object_name=object_name,
            expires=timedelta(days=days),
            response_headers=headers or None,
            version_id=version_id,
        )
        return url
    except S3Error as e:
        raise HTTPException(status_code=502, detail=f"MinIO presign error: {e.code}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"MinIO presign error: {e}")


async def ensure_file_access_allowed(
    session: AsyncSession,
    *,
    role: str,
    user_uuid: str,
    file_rec,
) -> None:
    """Raise HTTPException if the user is not allowed to access the file.

    Rules:
    - ADMIN: always allowed
    - Non-ADMIN: allowed if file's collection is public/hebees; otherwise offer_no must match
    """
    role_upper = (role or "").upper()
    if role_upper == "ADMIN":
        return

    try:
        user_no_bytes = uuid.UUID(user_uuid).bytes
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid x-user-uuid format (UUID required)")

    offer_no = await _get_offer_no_by_user(session, user_no_bytes)

    # Shared collections bypass (public / hebees)
    is_shared_collection = False
    if getattr(file_rec, "collection_no", None):
        res = await session.execute(
            select(Collection.name).where(Collection.collection_no == file_rec.collection_no)
        )
        col_name = res.scalar_one_or_none()
        if col_name and col_name in ("public", "hebees"):
            is_shared_collection = True

    if (not is_shared_collection) and (file_rec.offer_no != offer_no):
        raise HTTPException(status_code=403, detail="Forbidden: file does not belong to your offer")


async def generate_presigned_url_with_auth(
    session: AsyncSession,
    *,
    file_no: str,
    role: str,
    user_uuid: str,
    days: int = 7,
    inline: bool = False,
    content_type: str | None = None,
    version_id: str | None = None,
) -> str:
    """End-to-end helper: load file, check access, then return presigned URL."""
    try:
        file_no_bytes = uuid.UUID(file_no).bytes
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid fileNo format (UUID required)")

    file_rec = await FileRepository.find_by_file_no(session, file_no_bytes)
    if not file_rec:
        raise HTTPException(status_code=404, detail="File not found")

    await ensure_file_access_allowed(
        session,
        role=role,
        user_uuid=user_uuid,
        file_rec=file_rec,
    )

    return await get_presigned_url(
        bucket=file_rec.bucket,
        object_name=file_rec.path,
        content_type=content_type,
        days=days,
        version_id=version_id,
        inline=inline,
    )

