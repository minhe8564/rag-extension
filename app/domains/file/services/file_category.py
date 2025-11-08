from __future__ import annotations

from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.file_category import FileCategory
from ..schemas.response.file_category import FileCategoryListItem
from ....core.utils.uuid_utils import _bytes_to_uuid_str


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
