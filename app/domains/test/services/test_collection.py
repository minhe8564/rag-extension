import uuid
from typing import List, Optional
from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from ..models.test_collection import TestCollection
from ..schemas.response.test_collection import TestCollectionListItem


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
    cursor_created_at: Optional[datetime] = None,
    cursor_id: Optional[str] = None,
) -> List[TestCollection]:
    stmt = select(TestCollection)

    # ingest_no 필터 조건
    if ingest_no:
        stmt = stmt.where(TestCollection.ingest_group_no == _uuid_str_to_bytes(ingest_no))

    # ── 커서 기반 조건 추가 ──
    if cursor_created_at is not None and cursor_id is not None:
        stmt = stmt.where(
            or_(
                TestCollection.created_at < cursor_created_at,
                and_(
                    TestCollection.created_at == cursor_created_at,
                    TestCollection.test_collection_no < _uuid_str_to_bytes(cursor_id),
                ),
            )
        )

    # 최신순 정렬 + limit
    stmt = stmt.order_by(
        TestCollection.created_at.desc(),
        TestCollection.test_collection_no.desc(),
    ).limit(limit)

    res = await session.execute(stmt)
    rows = list(res.scalars().all())
    
        # ── DTO(TestCollectionListItem)로 변환 ──
    items = [
        TestCollectionListItem(
            testCollectionNo=_bytes_to_uuid_str(row.test_collection_no),
            name=row.name,
            ingestNo=_bytes_to_uuid_str(row.ingest_group_no),
            createdAt=row.created_at,
        )
        for row in rows
    ]
    
    return items
