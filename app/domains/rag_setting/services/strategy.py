from __future__ import annotations

from typing import List, Optional, Tuple
import uuid

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.strategy import Strategy, StrategyType


async def list_strategies(
    session: AsyncSession,
    type_filter: Optional[str] = None,
    page_num: int = 1,
    page_size: int = 20,
    sort_by: str = "name",
) -> Tuple[List[Strategy], int]:
    """
    전략 목록 조회

    Args:
        session: 데이터베이스 세션
        type_filter: 전략 유형 필터
        page_num: 페이지 번호
        page_size: 페이지 크기
        sort_by: 정렬 기준

    Returns:
        (전략 목록, 전체 항목 수)
    """
    # 기본 쿼리
    query = select(Strategy).options(selectinload(Strategy.strategy_type))

    # 타입 필터링
    if type_filter:
        query = query.join(Strategy.strategy_type).where(StrategyType.name == type_filter)

    # 정렬
    if sort_by == "name":
        query = query.order_by(Strategy.name.asc())
    else:
        query = query.order_by(Strategy.name.asc())

    # 전체 항목 수 조회
    count_query = select(func.count()).select_from(Strategy)
    if type_filter:
        count_query = count_query.join(Strategy.strategy_type).where(StrategyType.name == type_filter)

    result_count = await session.execute(count_query)
    total_items = result_count.scalar()

    # 페이지네이션
    offset = (page_num - 1) * page_size
    query = query.offset(offset).limit(page_size)

    # 데이터 조회
    result = await session.execute(query)
    strategies = result.scalars().all()

    return strategies, total_items


async def get_strategy_by_no(
    session: AsyncSession,
    strategy_no_str: str,
) -> Optional[Strategy]:
    """
    전략 상세 정보 조회

    Args:
        session: 데이터베이스 세션
        strategy_no_str: 전략 ID (UUID 문자열)

    Returns:
        Strategy 객체 또는 None
    """
    try:
        # UUID 문자열을 바이너리로 변환
        strategy_no_bytes = uuid.UUID(strategy_no_str).bytes
    except (ValueError, AttributeError):
        return None

    # 전략 조회 (strategy_type 관계 포함)
    query = (
        select(Strategy)
        .options(selectinload(Strategy.strategy_type))
        .where(Strategy.strategy_no == strategy_no_bytes)
    )

    result = await session.execute(query)
    strategy = result.scalar_one_or_none()

    return strategy
