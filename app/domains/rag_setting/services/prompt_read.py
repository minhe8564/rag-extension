"""
프롬프트 조회 서비스 (목록 + 상세)
"""
from __future__ import annotations

from typing import List, Tuple, Optional
import uuid

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.strategy import Strategy, StrategyType


async def list_prompts(
    session: AsyncSession,
    page_num: int = 1,
    page_size: int = 20,
    sort_by: str = "name"
) -> Tuple[List[Strategy], int]:
    """
    프롬프트 목록 조회 (페이지네이션 포함)

    strategy_type='prompting-system' 또는 'prompting-user'인 전략들을 조회합니다.

    Args:
        session: 데이터베이스 세션
        page_num: 페이지 번호 (1부터 시작)
        page_size: 페이지 크기
        sort_by: 정렬 기준 (기본: name)

    Returns:
        (프롬프트 목록, 전체 항목 수)
    """
    # 윈도우 함수를 사용한 전체 카운트 계산
    total_count_window = func.count().over().label('total_count')

    # 서브쿼리: 필터링과 정렬을 적용한 기본 쿼리
    # prompting-system과 prompting-user 모두 조회
    subquery = select(
        Strategy.strategy_no,
        Strategy.name,
        Strategy.description,
        Strategy.parameter,
        Strategy.strategy_type_no,
        total_count_window
    ).join(Strategy.strategy_type).where(
        StrategyType.name.in_(["prompting-system", "prompting-user"])
    )

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


async def get_prompt_by_no(
    session: AsyncSession,
    prompt_no_str: str
) -> Optional[Strategy]:
    """
    프롬프트 상세 정보 조회

    strategy_type='prompting-system' 또는 'prompting-user'인 전략만 조회합니다.

    Args:
        session: 데이터베이스 세션
        prompt_no_str: 프롬프트 ID (UUID 문자열)

    Returns:
        Strategy 객체 또는 None
    """
    try:
        # UUID 문자열을 바이너리로 변환
        prompt_no_bytes = uuid.UUID(prompt_no_str).bytes
    except (ValueError, AttributeError):
        return None

    # 프롬프트 조회 (strategy_type='prompting-system' 또는 'prompting-user'만 필터링)
    query = (
        select(Strategy)
        .join(Strategy.strategy_type)
        .options(selectinload(Strategy.strategy_type))
        .where(
            Strategy.strategy_no == prompt_no_bytes,
            StrategyType.name.in_(["prompting-system", "prompting-user"])
        )
    )

    result = await session.execute(query)
    prompt = result.scalar_one_or_none()

    return prompt
