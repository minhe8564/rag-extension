from __future__ import annotations

from io import BytesIO
from typing import Optional

from minio import Minio
from minio.error import S3Error

from ..config import settings


_client: Optional[Minio] = None


def get_minio_client() -> Minio:
    global _client
    if _client is None:
        if not settings.minio_endpoint or not settings.minio_access_key or not settings.minio_secret_key:
            raise RuntimeError("MinIO settings are not configured")
        _client = Minio(
            endpoint=settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=bool(settings.minio_secure),
        )
    return _client


def ensure_bucket(bucket_name: str) -> None:
    client = get_minio_client()
    # Only create if absent
    found = client.bucket_exists(bucket_name)
    if not found:
        client.make_bucket(bucket_name)


def object_exists(bucket_name: str, object_name: str) -> bool:
    client = get_minio_client()
    try:
        client.stat_object(bucket_name, object_name)
        return True
    except S3Error as e:
        if e.code in {"NoSuchKey", "NotFound", "NoSuchObject"}:
            return False
        raise


def put_object(bucket_name: str, object_name: str, data: bytes, content_type: str | None = None) -> None:
    client = get_minio_client()
    stream = BytesIO(data)
    length = len(data)
    client.put_object(
        bucket_name=bucket_name,
        object_name=object_name,
        data=stream,
        length=length,
        content_type=content_type or "application/octet-stream",
    )

