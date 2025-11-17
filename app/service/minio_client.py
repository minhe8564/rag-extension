from __future__ import annotations

from io import BytesIO
from typing import Optional

from minio import Minio
from minio.error import S3Error

from app.core.settings import settings


_client: Optional[Minio] = None


def get_minio_client() -> Minio:
    global _client
    if _client is None:
        endpoint = f"{settings.minio_host}:{settings.minio_port}"
        _client = Minio(
            endpoint=endpoint,
            access_key=settings.minio_username,
            secret_key=settings.minio_password,
            secure=False,
        )
    return _client


def ensure_bucket(bucket_name: str) -> None:
    client = get_minio_client()
    found = client.bucket_exists(bucket_name)
    if not found:
        client.make_bucket(bucket_name)


def put_object_bytes(bucket_name: str, object_name: str, data: bytes, content_type: str | None = None) -> None:
    client = get_minio_client()
    stream = BytesIO(data)
    length = len(data)
    client.put_object(
        bucket_name=bucket_name,
        object_name=object_name,
        data=stream,
        length=length,
        content_type=content_type or "text/plain; charset=utf-8",
    )


