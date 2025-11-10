from __future__ import annotations

from typing import List, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.test_file import TestFile
from ..schemas.response.test_file import TestFileListItem
from ....core.utils.uuid_utils import _bytes_to_uuid_str, _uuid_str_to_bytes

async def count_test_files(
    session: AsyncSession,
    *,
    test_collection_no: Optional[str] = None,
) -> int:
    stmt = select(func.count()).select_from(TestFile)
    if test_collection_no:
        stmt = stmt.where(TestFile.test_collection_no == _uuid_str_to_bytes(test_collection_no))
    res = await session.execute(stmt)
    return int(res.scalar() or 0)


async def list_test_files(
    session: AsyncSession,
    *,
    limit: int = 20,
    offset: int = 0,
    test_collection_no: Optional[str] = None,
) -> List[TestFileListItem]:
    stmt = select(TestFile)
    if test_collection_no:
        stmt = stmt.where(TestFile.test_collection_no == _uuid_str_to_bytes(test_collection_no))
    stmt = stmt.order_by(TestFile.created_at.desc()).limit(limit).offset(offset)

    res = await session.execute(stmt)
    rows = list(res.scalars().all())

    items = [
        TestFileListItem(
            testFileNo=_bytes_to_uuid_str(row.test_file_no),
            name=row.name,
            size=row.size,
            type=row.type,
            hash=row.hash,
            description=row.description,
            bucket=row.bucket,
            path=row.path,
            status=row.status,
            createdAt=row.created_at,
        )
        for row in rows
    ]
    return items

