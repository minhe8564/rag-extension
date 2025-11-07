from __future__ import annotations

from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.file import File
from ..schemas.response.files import FileListItem
from .common import _uuid_str_to_bytes, _bytes_to_uuid_str, _get_offer_no_by_user


async def list_files_by_offer(
    session: AsyncSession,
    *,
    user_no: str,
    limit: int = 20,
    offset: int = 0,
    category_no: Optional[str] = None,
) -> tuple[list[FileListItem], int]:
    user_no_bytes = _uuid_str_to_bytes(user_no)
    offer_no = await _get_offer_no_by_user(session, user_no_bytes)

    # Total count for pagination
    count_stmt = select(func.count()).select_from(File).where(File.bucket == offer_no)
    if category_no:
        count_stmt = count_stmt.where(File.file_category_no == _uuid_str_to_bytes(category_no))

    res_total = await session.execute(count_stmt)
    total_items = int(res_total.scalar() or 0)

    # Paged items
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

    return items, total_items

