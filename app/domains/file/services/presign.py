from __future__ import annotations

from datetime import timedelta
from pathlib import Path

from fastapi import HTTPException
from minio import Minio
from minio.error import S3Error

from app.core.settings import settings
from urllib.parse import urlparse


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

