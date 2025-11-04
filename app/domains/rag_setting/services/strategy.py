from __future__ import annotations

from typing import List, Optional, Tuple
import uuid

from sqlalchemy import select, func, over
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
    전략 목록 조회 (윈도우 함수를 사용한 최적화 버전)

    단일 쿼리로 데이터와 전체 카운트를 동시에 조회하여 성능을 개선하고,
    필터 조건의 동기화 문제를 방지합니다.

    Args:
        session: 데이터베이스 세션
        type_filter: 전략 유형 필터
        page_num: 페이지 번호
        page_size: 페이지 크기
        sort_by: 정렬 기준

    Returns:
        (전략 목록, 전체 항목 수)
    """
    # 윈도우 함수를 사용한 전체 카운트 계산
    # count() over()는 필터링된 결과 전체의 개수를 각 행에 포함시킴
    total_count_window = func.count().over().label('total_count')

    # 서브쿼리: 필터링과 정렬을 적용한 기본 쿼리
    subquery = select(
        Strategy.strategy_no,
        Strategy.name,
        Strategy.description,
        Strategy.strategy_type_no,
        Strategy.parameter,
        total_count_window
    )

    # 타입 필터링 (필요한 경우)
    if type_filter:
        subquery = subquery.join(Strategy.strategy_type).where(StrategyType.name == type_filter)

    # 정렬 (기본: 이름 오름차순)
    if sort_by == "name":
        subquery = subquery.order_by(Strategy.name.asc())
    else:
        subquery = subquery.order_by(Strategy.name.asc())

    # 페이지네이션 적용
    offset = (page_num - 1) * page_size
    subquery = subquery.offset(offset).limit(page_size)

    # 서브쿼리를 서브쿼리로 래핑
    subquery = subquery.subquery()

    # 최종 쿼리: Strategy 객체로 조회하면서 strategy_type 관계를 eager loading
    query = (
        select(Strategy, subquery.c.total_count)
        .join(subquery, Strategy.strategy_no == subquery.c.strategy_no)
        .options(selectinload(Strategy.strategy_type))
    )

    # 쿼리 실행
    result = await session.execute(query)
    rows = result.all()

    # 결과 분리
    if not rows:
        return [], 0

    strategies = [row[0] for row in rows]
    total_items = rows[0][1] if rows else 0

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
