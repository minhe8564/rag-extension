from __future__ import annotations

from typing import List, Optional, Tuple, Dict, Any
import uuid

from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.strategy import Strategy, StrategyType
from ..models.ingest_template import IngestGroup, ExtractionGroup, EmbeddingGroup


async def list_strategies(
    session: AsyncSession,
    type_filter: Optional[str] = None,
    page_num: int = 1,
    page_size: int = 20,
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

    # 정렬: 이름 오름차순 고정
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


async def list_strategy_types(
    session: AsyncSession,
) -> List[StrategyType]:
    """전략 유형 목록 조회"""

    query = select(StrategyType).order_by(StrategyType.name.asc())
    result = await session.execute(query)
    return result.scalars().all()


async def create_strategy_type(
    session: AsyncSession,
    name: str,
) -> StrategyType:
    """전략 유형 생성"""

    stmt = select(StrategyType).where(StrategyType.name == name)
    result = await session.execute(stmt)
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="동일한 이름의 전략 유형이 이미 존재합니다.",
        )

    strategy_type = StrategyType(name=name)
    session.add(strategy_type)
    await session.commit()
    await session.refresh(strategy_type)

    return strategy_type


async def update_strategy_type(
    session: AsyncSession,
    strategy_type_no_str: str,
    name: str,
) -> StrategyType:
    """전략 유형 이름 수정"""

    try:
        strategy_type_no_bytes = uuid.UUID(strategy_type_no_str).bytes
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="유효하지 않은 전략 유형 ID입니다.",
        )

    stmt = select(StrategyType).where(StrategyType.strategy_type_no == strategy_type_no_bytes)
    result = await session.execute(stmt)
    strategy_type = result.scalar_one_or_none()

    if not strategy_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="전략 유형을 찾을 수 없습니다.",
        )

    duplicate_stmt = select(StrategyType).where(StrategyType.name == name, StrategyType.strategy_type_no != strategy_type_no_bytes)
    duplicate_result = await session.execute(duplicate_stmt)
    if duplicate_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="동일한 이름의 전략 유형이 이미 존재합니다.",
        )

    strategy_type.name = name
    await session.commit()
    await session.refresh(strategy_type)

    return strategy_type


async def delete_strategy_type(
    session: AsyncSession,
    strategy_type_no_str: str,
) -> None:
    """전략 유형 삭제"""

    try:
        strategy_type_no_bytes = uuid.UUID(strategy_type_no_str).bytes
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="유효하지 않은 전략 유형 ID입니다.",
        )

    stmt = select(StrategyType).where(StrategyType.strategy_type_no == strategy_type_no_bytes)
    result = await session.execute(stmt)
    strategy_type = result.scalar_one_or_none()

    if not strategy_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="전략 유형을 찾을 수 없습니다.",
        )

    usage_stmt = select(Strategy.strategy_no).where(Strategy.strategy_type_no == strategy_type_no_bytes).limit(1)
    usage_result = await session.execute(usage_stmt)
    if usage_result.first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="해당 전략 유형을 사용하는 전략이 존재합니다.",
        )

    await session.delete(strategy_type)
    await session.commit()


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


async def create_strategy(
    session: AsyncSession,
    name: str,
    code: str,
    description: str,
    parameter: Optional[Dict[str, Any]],
    strategy_type_name: str,
) -> Strategy:
    """
    새로운 전략 생성

    Args:
        session: 데이터베이스 세션
        name: 전략명
        code: 전략 코드
        description: 전략 설명
        parameter: 전략 파라미터
        strategy_type_name: 전략 유형 이름

    Returns:
        생성된 Strategy 객체

    Raises:
        HTTPException: 전략 유형을 찾을 수 없거나 동일 이름의 전략이 존재하는 경우
    """

    code_value = (code or '').strip()
    if not code_value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="전략 코드는 필수 값입니다.",
        )

    # 전략 유형 조회
    stmt = select(StrategyType).where(StrategyType.name == strategy_type_name)
    result = await session.execute(stmt)
    strategy_type = result.scalar_one_or_none()

    if not strategy_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="전략 유형을 찾을 수 없습니다.",
        )

    # 동일 이름 전략 여부 확인 (해당 유형 내)
    duplicate_stmt = select(Strategy).where(
        Strategy.name == name,
        Strategy.strategy_type_no == strategy_type.strategy_type_no,
    )
    duplicate_result = await session.execute(duplicate_stmt)
    if duplicate_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="동일한 이름의 전략이 이미 존재합니다.",
        )

    strategy = Strategy(
        name=name,
        code=code_value,
        description=description,
        parameter=parameter or {},
        strategy_type_no=strategy_type.strategy_type_no,
    )

    session.add(strategy)
    await session.commit()
    await session.refresh(strategy)

    return strategy

async def update_strategy(
    session: AsyncSession,
    strategy_no_str: str,
    name: str,
    code: Optional[str],
    description: str,
    parameter: Optional[Dict[str, Any]],
    strategy_type_name: Optional[str] = None,
) -> Strategy:
    """전략 수정"""

    try:
        strategy_no_bytes = uuid.UUID(strategy_no_str).bytes
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="유효하지 않은 전략 ID입니다.",
        )

    stmt = select(Strategy).options(selectinload(Strategy.strategy_type)).where(Strategy.strategy_no == strategy_no_bytes)
    result = await session.execute(stmt)
    strategy = result.scalar_one_or_none()

    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="전략을 찾을 수 없습니다.",
        )

    # 유형 변경이 요청된 경우 이름으로 조회
    if strategy_type_name:
        type_stmt = select(StrategyType).where(StrategyType.name == strategy_type_name)
        type_result = await session.execute(type_stmt)
        strategy_type = type_result.scalar_one_or_none()

        if not strategy_type:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="전략 유형을 찾을 수 없습니다.",
            )

        strategy.strategy_type_no = strategy_type.strategy_type_no
        strategy.strategy_type = strategy_type

    # 동일 이름 중복 여부 확인 (같은 타입 내에서)
    type_no_for_duplicate = strategy.strategy_type_no
    duplicate_stmt = select(Strategy).where(
        Strategy.name == name,
        Strategy.strategy_type_no == type_no_for_duplicate,
        Strategy.strategy_no != strategy_no_bytes,
    )
    duplicate_result = await session.execute(duplicate_stmt)
    if duplicate_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="동일한 이름의 전략이 이미 존재합니다.",
        )

    code_value: Optional[str] = None
    if code is not None:
        code_value = code.strip()
        if not code_value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="전략 코드는 비워둘 수 없습니다.",
            )

    strategy.name = name
    strategy.description = description
    strategy.parameter = parameter or {}
    if code_value is not None:
        strategy.code = code_value

    await session.commit()
    await session.refresh(strategy)

    return strategy

async def delete_strategy(
    session: AsyncSession,
    strategy_no_str: str,
) -> None:
    """
    전략 삭제

    Args:
        session: 데이터베이스 세션
        strategy_no_str: 전략 ID (UUID 문자열)

    Raises:
        HTTPException: 전략을 찾을 수 없거나 템플릿에서 사용 중인 경우
    """

    try:
        strategy_no_bytes = uuid.UUID(strategy_no_str).bytes
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="유효하지 않은 전략 ID입니다.",
        )

    query = select(Strategy).where(Strategy.strategy_no == strategy_no_bytes)
    result = await session.execute(query)
    strategy = result.scalar_one_or_none()

    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="전략을 찾을 수 없습니다.",
        )

    chunking_usage = await session.execute(
        select(IngestGroup.ingest_group_no)
        .where(IngestGroup.chunking_strategy_no == strategy_no_bytes)
        .limit(1)
    )

    extraction_usage = await session.execute(
        select(ExtractionGroup.extraction_group_no)
        .where(ExtractionGroup.extraction_strategy_no == strategy_no_bytes)
        .limit(1)
    )

    embedding_usage = await session.execute(
        select(EmbeddingGroup.embedding_group_no)
        .where(EmbeddingGroup.embedding_strategy_no == strategy_no_bytes)
        .limit(1)
    )

    if chunking_usage.first() or extraction_usage.first() or embedding_usage.first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="해당 전략을 사용하는 템플릿이 존재합니다.",
        )

    await session.delete(strategy)
    await session.commit()
