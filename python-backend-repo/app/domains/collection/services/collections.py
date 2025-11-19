from __future__ import annotations

import uuid
from typing import List

from fastapi import HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.user.models.user import User
from ..models.collection import Collection
from ..schemas.response.collection import CollectionListItem
from app.domains.file.models.file import File
from app.domains.file.schemas.response.files import FileListItem


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


async def list_collections(
    session: AsyncSession,
    *,
    limit: int = 20,
    offset: int = 0,
) -> tuple[List[CollectionListItem], int]:

    # Total count for pagination
    count_stmt = select(func.count()).select_from(Collection)
    res_total = await session.execute(count_stmt)
    total_items = int(res_total.scalar() or 0)

    # Paged items
    stmt = (
        select(Collection)
        .order_by(Collection.created_at.desc())
        .limit(limit)
        .offset(offset)
    )

    res = await session.execute(stmt)
    rows = list(res.scalars().all())

    items = [
        CollectionListItem(
            collectionNo=_bytes_to_uuid_str(row.collection_no),
            name=row.name,
            version=row.version,
            ingestGroupNo=_bytes_to_uuid_str(row.ingest_group_no),
            createdAt=row.created_at,
        )
        for row in rows
    ]
    return items, total_items

async def list_filtered_collections(
    session: AsyncSession,
    *,
    limit: int = 5,
    offset: int = 0,
) -> tuple[List[CollectionListItem], int]:
    count_stmt = (
        select(func.count(func.distinct(Collection.collection_no)))
        .select_from(Collection)
        .where(Collection.name.in_(["public", "hebees"]))
    )
    res_total = await session.execute(count_stmt)
    total_items = int(res_total.scalar() or 0)
    stmt = (
        select(Collection)
        .where(Collection.name.in_(["public", "hebees"]))
        .order_by(Collection.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    res = await session.execute(stmt)
    rows = list(res.scalars().all())
    items = [
        CollectionListItem(
            collectionNo=_bytes_to_uuid_str(row.collection_no),
            name=row.name,
            version=row.version,
            ingestGroupNo=_bytes_to_uuid_str(row.ingest_group_no),
            createdAt=row.created_at,
        )
        for row in rows
    ]
    return items, total_items


async def list_files_in_collection(
    session: AsyncSession,
    *,
    user_no: str,
    collection_no: str,
    limit: int = 5,
    offset: int = 0,
) -> tuple[List[FileListItem], int]:
    user_no_bytes = _uuid_str_to_bytes(user_no)
    collection_no_bytes = _uuid_str_to_bytes(collection_no)

    stmt_check = (
        select(Collection.collection_no)
        .where(
            Collection.collection_no == collection_no_bytes,
        )
    )
    res_check = await session.execute(stmt_check)
    if res_check.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="컬렉션을 찾을 수 없거나 접근할 수 없습나다.")

    # Total count for pagination within the collection
    count_stmt = select(func.count()).select_from(File).where(File.collection_no == collection_no_bytes)
    res_total = await session.execute(count_stmt)
    total_items = int(res_total.scalar() or 0)

    # List files in the collection (paged)
    stmt = (
        select(File)
        .where(File.collection_no == collection_no_bytes)
        .order_by(File.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    res = await session.execute(stmt)
    rows = list(res.scalars().all())

    items = [
        FileListItem(
            fileNo=_bytes_to_uuid_str(row.file_no),
            name=row.name,
            size=row.size,
            type=row.type,
            bucket=row.bucket,
            path=row.path,
            status=row.status,
            categoryNo=_bytes_to_uuid_str(row.file_category_no),
            collectionNo=_bytes_to_uuid_str(row.collection_no) if row.collection_no else None,
            createdAt=row.created_at,
        )
        for row in rows
    ]
    return items, total_items
