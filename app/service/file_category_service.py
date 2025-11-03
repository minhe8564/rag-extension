from __future__ import annotations

from typing import List
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.file_category import FileCategory
from ..schemas.file_category import FileCategoryListItem


def _bytes_to_uuid_str(b: bytes) -> str:
    try:
        return str(uuid.UUID(bytes=b))
    except Exception:
        return b.hex()


async def list_file_categories(session: AsyncSession) -> List[FileCategoryListItem]:
    stmt = select(FileCategory).order_by(FileCategory.created_at.asc())
    result = await session.execute(stmt)
    rows = result.scalars().all()
    return [
        FileCategoryListItem(
            categoryNo=_bytes_to_uuid_str(row.file_category_no),
            name=row.name,
        )
        for row in rows
    ]

