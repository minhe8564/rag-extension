from __future__ import annotations

import hashlib
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import settings
from app.core.minio_client import ensure_bucket, object_exists, put_object
from app.domains.user.models.user import User
from ..models.file import File
from ..models.file_category import FileCategory
from app.domains.collection.models.collection import Collection
from ..schemas.response.files import FileListItem


def _uuid_str_to_bytes(u: str) -> bytes:
    return uuid.UUID(u).bytes


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
    b = (input_bucket or "private").lower()
    if b == "public":
        return (getattr(settings, "default_public_bucket", None) or "public"), False
    if b == "test":
        return (getattr(settings, "default_test_bucket", None) or "test"), False
    # private/personal bucket
    return offer_no, True


def _build_object_key(category_no: str, filename: str) -> str:
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
) -> str:
    # MinIO helpers provided by app.core.minio_client
    # Validate inputs and derive required values
    user_no_bytes = _uuid_str_to_bytes(user_no)
    category_no_bytes = _uuid_str_to_bytes(category_no)
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
    object_key = _build_object_key(category_no, object_filename)

    exists = object_exists(bucket_name, object_key)
    policy = (on_name_conflict or "reject").lower()
    if exists:
        if policy == "reject":
            raise HTTPException(status_code=409, detail="동일한 파일명이 이미 존재합니다.")
        elif policy == "rename":
            # regenerate UUID-based object key until unique (few attempts)
            attempts = 0
            while object_exists(bucket_name, object_key) and attempts < 5:
                new_uuid = uuid.uuid4()
                file_no_bytes = new_uuid.bytes
                file_id_str = str(new_uuid)
                object_filename = file_id_str + (ext_with_dot or "")
                object_key = _build_object_key(category_no, object_filename)
                attempts += 1
        elif policy == "overwrite":
            pass
        else:
            raise HTTPException(status_code=400, detail="onNameConflict 값이 올바르지 않습니다.")

    # Upload to MinIO
    put_object(bucket_name, object_key, file_bytes, content_type or "application/octet-stream")

    # Persist into DB
    now = datetime.now()

    # Validate optional FKs to avoid FK errors
    collection_no_bytes = _uuid_str_to_bytes(collection_no) if collection_no else None
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
        source_no=_uuid_str_to_bytes(source_no) if source_no else None,
        collection_no=collection_no_bytes,
        created_at=now,
        updated_at=now,
    )

    session.add(entity)
    await session.flush()
    await session.commit()

    return _bytes_to_uuid_str(file_no_bytes)


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
