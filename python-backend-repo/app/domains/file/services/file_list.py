from __future__ import annotations

from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ...collection.models.collection import Collection
from ..models.file import File
from ..schemas.response.files import FileListItem
from ....core.utils.uuid_utils import _uuid_str_to_bytes, _bytes_to_uuid_str, _get_offer_no_by_user


async def list_files_by_collection(
    session: AsyncSession,
    *,
    user_no: str,
    limit: int = 20,
    offset: int = 0,
    category_no: Optional[str] = None,
) -> tuple[list[FileListItem], int]:
    user_no_bytes = _uuid_str_to_bytes(user_no)
    offer_no = await _get_offer_no_by_user(session, user_no_bytes)
    collection_no_subq = (
        select(Collection.collection_no)
        .where(Collection.offer_no == offer_no)
        .order_by(Collection.version.desc())
        .limit(1)
        .scalar_subquery()
    )

    category_no_bytes: Optional[bytes] = _uuid_str_to_bytes(category_no) if category_no else None

    # Single query using window function to get total count alongside paged rows
    stmt = (
        select(
            File,
            func.count().over().label("total_count"),
        )
        .where(File.collection_no == collection_no_subq)
    )
    if category_no_bytes is not None:
        stmt = stmt.where(File.file_category_no == category_no_bytes)

    stmt = stmt.order_by(File.created_at.desc()).limit(limit).offset(offset)

    res = await session.execute(stmt)
    records = list(res.all())

    if not records:
        # No files (either no collection or empty collection)
        return [], 0

    # total_count is the same for all rows due to window function
    total_items = int(records[0].total_count or 0)

    items: list[FileListItem] = []
    for file_row, _total in records:
        items.append(
            FileListItem(
                fileNo=_bytes_to_uuid_str(file_row.file_no),
                name=file_row.name,
                size=file_row.size,
                type=file_row.type,
                bucket=file_row.bucket,
                path=file_row.path,
                status=file_row.status,
                categoryNo=_bytes_to_uuid_str(file_row.file_category_no),
                collectionNo=_bytes_to_uuid_str(file_row.collection_no) if file_row.collection_no else None,
                createdAt=file_row.created_at,
            )
        )

    return items, total_items

