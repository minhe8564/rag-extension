from __future__ import annotations

import hashlib
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clients.minio_client import ensure_bucket, object_exists, put_object

from app.domains.collection.models.collection import Collection
from ..models.file import File
from ..schemas.response.upload_files import IngestFileMeta, UploadBatchMeta
from app.core.utils.uuid_utils import (
    _uuid_str_to_bytes,
    _bytes_to_uuid_str,
    _get_offer_no_by_user,
    _ensure_category_exists,
    _resolve_bucket,
    _build_presigned_key,
    _split_name_ext,
    _handle_name_conflict,
)


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
    user_role: Optional[str] = None,
) -> tuple[str, IngestFileMeta]:
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

    # Conflict handling by filename within bucket/category
    original_name = Path(original_filename).name
    policy = (on_name_conflict or "reject").lower()
    await _handle_name_conflict(
        session,
        bucket_name=bucket_name,
        category_no_bytes=category_no_bytes,
        original_name=original_name,
        policy=policy,
        user_role=user_role,
    )

    # Upload to MinIO
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
        status="INGESTING",
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
    user_role: Optional[str] = None,
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
            user_role=user_role,
        )
        created_nos.append(file_no)
        ingest_file_metas.append(file_meta)

    batch_meta = UploadBatchMeta(bucket=bucket_name, offerNo=offer_no, files=ingest_file_metas)
    return batch_meta, created_nos
