from __future__ import annotations

import uuid
from typing import List, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.test_file import TestFile
from ..schemas.response.test_file import TestFileListItem


def _bytes_to_uuid_str(b: bytes) -> str:
    try:
        return str(uuid.UUID(bytes=b))
    except Exception:
        return b.hex()

def _uuid_str_to_bytes(s: str) -> bytes:
    try:
        return uuid.UUID(s).bytes
    except Exception:
        # Accept hex without dashes
        try:
            return uuid.UUID(hex=s).bytes
        except Exception:
            raise ValueError("Invalid UUID format")

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
            createdAt=row.created_at,
        )
        for row in rows
    ]
    return items

