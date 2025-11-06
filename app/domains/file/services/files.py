from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Tuple
import logging

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import settings
from app.core.minio_client import ensure_bucket, object_exists, put_object, get_minio_client
from minio.error import S3Error
from urllib.parse import urlparse, urlunparse
from app.domains.user.models.user import User
from ..models.file import File
from ..models.file_category import FileCategory
from app.domains.collection.models.collection import Collection
from ..schemas.response.files import FileListItem
from ..schemas.response.upload_files import IngestFileMeta, UploadBatchMeta


logger = logging.getLogger(__name__)


def _uuid_str_to_bytes(u: str, *, field_name: Optional[str] = None) -> bytes:
    try:
        return uuid.UUID(u).bytes
    except Exception:
        fn = field_name or "uuid"
        # Log and raise a client error so it doesn't surface as 500
        try:
            logger.warning("Invalid UUID for %s: %r", fn, u)
        except Exception:
            pass
        raise HTTPException(
            status_code=400,
            detail={
                "message": f"Invalid {fn} format (UUID required)",
                "field": fn,
            },
        )


def _bytes_to_uuid_str(b: bytes) -> str:
    try:
        return str(uuid.UUID(bytes=b))
    except Exception:
        return b.hex()


async def _get_offer_no_by_user(session: AsyncSession, user_no_bytes: bytes) -> str:
    stmt = select(User.offer_no).where(User.user_no == user_no_bytes)
    res = await session.execute(stmt)
    offer_no = res.scalar_one_or_none()
    if offer_no is None:
        raise HTTPException(status_code=400, detail="존재하지 않는 사용자입니다.")
    return offer_no


async def _ensure_category_exists(session: AsyncSession, category_no_bytes: bytes) -> None:
    stmt = select(FileCategory.file_category_no).where(FileCategory.file_category_no == category_no_bytes)
    res = await session.execute(stmt)
    if res.scalar_one_or_none() is None:
        raise HTTPException(status_code=400, detail="존재하지 않는 카테고리입니다.")


def _resolve_bucket(input_bucket: Optional[str], offer_no: str) -> tuple[str, bool]:
    # returns (bucket_name, should_create)
    # If explicit bucket is provided, use it as-is (ADMIN flow), creating if needed.
    if input_bucket:
        b = input_bucket.strip()
        lb = b.lower()
        if lb == "public":
            return (getattr(settings, "default_public_bucket", None) or "public"), False
        if lb == "hebees":
            return (getattr(settings, "default_hebees_bucket", None) or "hebees"), False
        return b, True
    # Otherwise use personal (offer_no) bucket (USER flow)
    return offer_no, True


def _build_presigned_key(category_no: str, filename: str) -> str:
    safe_name = Path(filename).name
    return f"{category_no}/{safe_name}"


def _split_name_ext(filename: str) -> tuple[str, str]:
    p = Path(filename).name
    stem = Path(p).stem
    ext = Path(p).suffix  # includes dot or empty
    return stem, ext

async def upload_file(
    session: AsyncSession,
    *,
    file_bytes: bytes,
    original_filename: str,
    content_type: Optional[str],
    user_no: str,
    category_no: str,
    on_name_conflict: str = "reject",
    bucket: Optional[str] = None,
    collection_no: Optional[str] = None,
    source_no: Optional[str] = None,
) -> tuple[str, IngestFileMeta]:
    # MinIO helpers provided by app.core.minio_client
    # Validate inputs and derive required values
    user_no_bytes = _uuid_str_to_bytes(user_no, field_name="userNo")
    category_no_bytes = _uuid_str_to_bytes(category_no, field_name="categoryNo")
    await _ensure_category_exists(session, category_no_bytes)
    offer_no = await _get_offer_no_by_user(session, user_no_bytes)

    bucket_name, should_create = _resolve_bucket(bucket, offer_no)
    if should_create:
        ensure_bucket(bucket_name)

    # File metadata
    size = len(file_bytes)
    sha256 = hashlib.sha256(file_bytes).hexdigest()
    stem, ext_with_dot = _split_name_ext(original_filename)
    ext = (ext_with_dot[1:] if ext_with_dot.startswith(".") else ext_with_dot).lower()

    # Conflict handling
    original_name = Path(original_filename).name
    file_no_bytes = uuid.uuid4().bytes
    file_id_str = str(uuid.UUID(bytes=file_no_bytes))
    object_filename = file_id_str + (ext_with_dot or "")
    object_key = _build_presigned_key(category_no, object_filename)

    exists = object_exists(bucket_name, object_key)
    policy = (on_name_conflict or "reject").lower()
    if exists:
        if policy == "reject":
            raise HTTPException(status_code=409, detail="동일한 파일명이 이미 존재합니다.")
        elif policy == "overwrite":
            pass
        else:
            raise HTTPException(status_code=400, detail="onNameConflict 값이 올바르지 않습니다.")

    # Upload to MinIO
    put_object(bucket_name, object_key, file_bytes, content_type or "application/octet-stream")

    # Persist into DB
    now = datetime.now()

    # Validate optional FKs to avoid FK errors
    collection_no_bytes = _uuid_str_to_bytes(collection_no, field_name="collectionNo") if collection_no else None
    if collection_no_bytes is not None:
        stmt = select(Collection.collection_no).where(Collection.collection_no == collection_no_bytes)
        res = await session.execute(stmt)
        if res.scalar_one_or_none() is None:
            raise HTTPException(status_code=400, detail="존재하지 않는 컬렉션입니다.")

    entity = File(
        file_no=file_no_bytes,
        user_no=user_no_bytes,
        name=original_name,
        size=size,
        type=ext or "",
        hash=sha256,
        description="",
        bucket=bucket_name,
        path=object_key,
        file_category_no=category_no_bytes,
        offer_no=offer_no,
        source_no=_uuid_str_to_bytes(source_no, field_name="sourceNo") if source_no else None,
        collection_no=collection_no_bytes,
        created_at=now,
        updated_at=now,
    )

    session.add(entity)
    await session.flush()
    await session.commit()

    return _bytes_to_uuid_str(file_no_bytes), IngestFileMeta(
        fileNo=_bytes_to_uuid_str(file_no_bytes),
        fileType=ext or "",
        fileName=original_name,
        path=object_key,
    )


async def upload_files(
    session: AsyncSession,
    *,
    files: list[tuple[bytes, str, Optional[str]]],
    user_no: str,
    category_no: str,
    on_name_conflict: str = "reject",
    bucket: Optional[str] = None,
    collection_no: Optional[str] = None,
    source_no: Optional[str] = None,
) -> tuple[UploadBatchMeta, list[str]]:
    # Resolve user and bucket once
    user_no_bytes = _uuid_str_to_bytes(user_no, field_name="userNo")
    category_no_bytes = _uuid_str_to_bytes(category_no, field_name="categoryNo")
    await _ensure_category_exists(session, category_no_bytes)
    offer_no = await _get_offer_no_by_user(session, user_no_bytes)

    bucket_name, should_create = _resolve_bucket(bucket, offer_no)
    if should_create:
        ensure_bucket(bucket_name)

    # Preflight duplicate check when policy is reject
    policy = (on_name_conflict or "reject").lower()
    if policy == "reject":
        names = [Path(n).name for _, n, _ in files]
        # intra-batch duplicates
        seen: set[str] = set()
        intra_dups: set[str] = set()
        for n in names:
            if n in seen:
                intra_dups.add(n)
            else:
                seen.add(n)

        # existing duplicates within bucket/category
        stmt = (
            select(File.name)
            .where(File.bucket == bucket_name)
            .where(File.file_category_no == category_no_bytes)
            .where(File.name.in_(set(names)))
        )
        res = await session.execute(stmt)
        existing_dups = set(res.scalars().all())

        conflicts = sorted(set(intra_dups) | set(existing_dups))
        if conflicts:
            raise HTTPException(status_code=409, detail={"message": "Duplicate filenames", "conflicts": conflicts})

    # Proceed to upload each
    created_nos: list[str] = []
    ingest_file_metas: list[IngestFileMeta] = []
    for file_bytes, original_filename, content_type in files:
        file_no, file_meta = await upload_file(
            session,
            file_bytes=file_bytes,
            original_filename=original_filename,
            content_type=content_type,
            user_no=user_no,
            category_no=category_no,
            on_name_conflict=on_name_conflict,
            bucket=bucket_name,
            collection_no=collection_no,
            source_no=source_no,
        )
        created_nos.append(file_no)
        ingest_file_metas.append(file_meta)

    batch_meta = UploadBatchMeta(bucket=bucket_name, offerNo=offer_no, files=ingest_file_metas)
    return batch_meta, created_nos


async def list_files_by_offer(
    session: AsyncSession,
    *,
    user_no: str,
    limit: int = 20,
    offset: int = 0,
    category_no: Optional[str] = None,
) -> list[FileListItem]:
    user_no_bytes = _uuid_str_to_bytes(user_no)
    offer_no = await _get_offer_no_by_user(session, user_no_bytes)

    stmt = (
        select(File)
        .where(File.bucket == offer_no)
        .order_by(File.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    if category_no:
        stmt = stmt.where(File.file_category_no == _uuid_str_to_bytes(category_no))

    res = await session.execute(stmt)
    rows = list(res.scalars().all())

    items: list[FileListItem] = []
    for row in rows:
        items.append(
            FileListItem(
                fileNo=_bytes_to_uuid_str(row.file_no),
                name=row.name,
                size=row.size,
                type=row.type,
                bucket=row.bucket,
                path=row.path,
                categoryNo=_bytes_to_uuid_str(row.file_category_no),
                collectionNo=_bytes_to_uuid_str(row.collection_no) if row.collection_no else None,
                createdAt=row.created_at,
            )
        )

    return items


async def get_presigned_url(
    *,
    bucket: str,
    object_name: str,
    content_type: str | None = None,
    days: int = 7,
    version_id: str | None = None,
    inline: bool = True,
) -> str:
    """Generate a presigned GET URL for an object in MinIO.

    - bucket: Target bucket name
    - object_name: Full object key (including any path)
    - content_type: Optional content-type for response header
    - days: Expiration in days (1-7)
    - version_id: Optional version id if versioning is enabled
    - inline: If True, set Content-Disposition to inline; otherwise attachment
    """
    logger.debug(f"[FILE] presigned 요청: bucket={bucket}, object={object_name}")

    # Clamp expiration to [1, 7]
    days = max(1, min(days, 7))

    disposition = "inline" if inline else "attachment"
    safe_name = Path(object_name).name
    headers: dict[str, str] = {
        "response-content-disposition": f'{disposition}; filename="{safe_name}"',
    }
    if content_type:
        headers["response-content-type"] = content_type

    client = get_minio_client()
    try:
        url = client.presigned_get_object(
            bucket_name=bucket,
            object_name=object_name,
            expires=timedelta(days=days),
            response_headers=headers or None,
            version_id=version_id,
        )

        # If a public endpoint is configured that differs from the API endpoint,
        # rewrite the presigned URL to use the public base (keeps path/query).
        public_base = settings.minio_public_endpoint_url
        api_base = settings.minio_endpoint_url
        if public_base and api_base and public_base != api_base:
            parsed_url = urlparse(url)
            public_parsed = urlparse(public_base)
            url = urlunparse(
                (
                    public_parsed.scheme,
                    public_parsed.netloc,
                    parsed_url.path,
                    parsed_url.params,
                    parsed_url.query,
                    parsed_url.fragment,
                )
            )

        return url
    except S3Error as e:
        logger.error(f"[FILE] presign 실패: {e.code} {e.message}")
        raise HTTPException(status_code=502, detail=f"MinIO presign error: {e.code}")
    except Exception as e:
        logger.error(f"[FILE] presign 실패(기타): {e}")
        raise HTTPException(status_code=500, detail=f"MinIO presign error: {e}")
