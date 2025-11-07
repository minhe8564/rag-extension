import uuid
from typing import List, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession


from ..models.test_collection import TestCollection


def _bytes_to_uuid_str(b: bytes) -> str:
    try:
        return str(uuid.UUID(bytes=b))
    except Exception:
        return b.hex()


def _uuid_str_to_bytes(u: str) -> bytes:
    return uuid.UUID(u).bytes

async def count_test_collections(session: AsyncSession) -> int:
    stmt = select(func.count()).select_from(TestCollection)
    result = await session.execute(stmt)
    return result.scalar_one()


async def list_test_collections(
    session: AsyncSession,
    *,
    ingest_no: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
) -> List[TestCollection]:
    stmt = select(TestCollection)
    if ingest_no:
        stmt = stmt.where(TestCollection.ingest_group_no == _uuid_str_to_bytes(ingest_no))
    stmt = stmt.order_by(TestCollection.created_at.desc()).limit(limit).offset(offset)

    res = await session.execute(stmt)
    return list(res.scalars().all())
