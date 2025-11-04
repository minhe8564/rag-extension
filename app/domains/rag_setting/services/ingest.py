from __future__ import annotations

from typing import List, Tuple, Optional
import uuid

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from ..models.ingest_template import IngestGroup, uuid_to_binary, binary_to_uuid
from ..models.strategy import Strategy


async def list_ingest_groups(
    session: AsyncSession,
    page_num: int = 1,
    page_size: int = 20,
    sort_by: str = "created_at",
) -> Tuple[List[IngestGroup], int]:
    """
    Ingest 그룹 목록 조회 (윈도우 함수를 사용한 최적화 버전)

    단일 쿼리로 데이터와 전체 카운트를 동시에 조회하여 성능을 개선하고,
    필터 조건의 동기화 문제를 방지합니다.

    Args:
        session: 데이터베이스 세션
        page_num: 페이지 번호
        page_size: 페이지 크기
        sort_by: 정렬 기준

    Returns:
        (Ingest 그룹 목록, 전체 항목 수)
    """
    # 윈도우 함수를 사용한 전체 카운트 계산
    # count() over()는 필터링된 결과 전체의 개수를 각 행에 포함시킴
    total_count_window = func.count().over().label('total_count')

    # 서브쿼리: 필터링과 정렬을 적용한 기본 쿼리
    subquery = select(
        IngestGroup.ingest_group_no,
        IngestGroup.is_default,
        IngestGroup.extraction_strategy_no,
        IngestGroup.chunking_strategy_no,
        IngestGroup.embedding_strategy_no,
        IngestGroup.extraction_parameter,
        IngestGroup.chunking_parameter,
        IngestGroup.embedding_parameter,
        total_count_window
    )

    # 정렬 (기본: 생성일자 내림차순)
    if sort_by == "created_at":
        subquery = subquery.order_by(IngestGroup.created_at.desc())
    else:
        subquery = subquery.order_by(IngestGroup.created_at.desc())

    # 페이지네이션 적용
    offset = (page_num - 1) * page_size
    subquery = subquery.offset(offset).limit(page_size)

    # 서브쿼리를 서브쿼리로 래핑
    subquery = subquery.subquery()

    # 최종 쿼리: IngestGroup 객체로 조회하면서 strategy 관계를 eager loading
    query = (
        select(IngestGroup, subquery.c.total_count)
        .join(subquery, IngestGroup.ingest_group_no == subquery.c.ingest_group_no)
        .options(
            selectinload(IngestGroup.extraction_strategy),
            selectinload(IngestGroup.chunking_strategy),
            selectinload(IngestGroup.embedding_strategy)
        )
    )

    # 쿼리 실행
    result = await session.execute(query)
    rows = result.all()

    # 결과 분리
    if not rows:
        return [], 0

    groups = [row[0] for row in rows]
    total_items = rows[0][1] if rows else 0

    return groups, total_items


async def verify_strategy_exists(
    session: AsyncSession,
    strategy_no: str,
) -> Optional[Strategy]:
    """
    전략 존재 여부 확인

    Args:
        session: 데이터베이스 세션
        strategy_no: 전략 ID (UUID 문자열)

    Returns:
        Strategy 객체 또는 None
    """
    try:
        strategy_binary = uuid_to_binary(strategy_no)
    except ValueError:
        return None

    query = select(Strategy).where(Strategy.strategy_no == strategy_binary)
    result = await session.execute(query)
    return result.scalar_one_or_none()


async def create_ingest_template(
    session: AsyncSession,
    name: str,
    is_default: bool,
    extraction_no: str,
    extraction_parameters: dict,
    chunking_no: str,
    chunking_parameters: dict,
    embedding_no: str,
    embedding_parameters: dict,
) -> str:
    """
    Ingest 템플릿 생성

    Args:
        session: 데이터베이스 세션
        name: 템플릿 이름 (현재 미사용, 향후 확장 가능)
        is_default: 기본 템플릿 여부
        extraction_no: 추출 전략 ID
        extraction_parameters: 추출 전략 파라미터
        chunking_no: 청킹 전략 ID
        chunking_parameters: 청킹 전략 파라미터
        embedding_no: 임베딩 전략 ID
        embedding_parameters: 임베딩 전략 파라미터

    Returns:
        생성된 Ingest 템플릿 ID (UUID 문자열)

    Raises:
        HTTPException: 전략을 찾을 수 없는 경우
    """
    # 전략 존재 여부 확인
    extraction_strategy = await verify_strategy_exists(session, extraction_no)
    if not extraction_strategy:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"추출 전략을 찾을 수 없습니다: {extraction_no}"
        )

    chunking_strategy = await verify_strategy_exists(session, chunking_no)
    if not chunking_strategy:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"청킹 전략을 찾을 수 없습니다: {chunking_no}"
        )

    embedding_strategy = await verify_strategy_exists(session, embedding_no)
    if not embedding_strategy:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"임베딩 전략을 찾을 수 없습니다: {embedding_no}"
        )

    # 기본 템플릿 설정 시 기존 기본 템플릿 해제
    if is_default:
        query = select(IngestGroup).where(IngestGroup.is_default == True)
        result = await session.execute(query)
        existing_defaults = result.scalars().all()
        for existing in existing_defaults:
            existing.is_default = False

    # Ingest 그룹 생성
    ingest_group = IngestGroup(
        is_default=is_default,
        extraction_strategy_no=uuid_to_binary(extraction_no),
        chunking_strategy_no=uuid_to_binary(chunking_no),
        embedding_strategy_no=uuid_to_binary(embedding_no),
        extraction_parameter=extraction_parameters or {},
        chunking_parameter=chunking_parameters or {},
        embedding_parameter=embedding_parameters or {},
    )

    session.add(ingest_group)
    await session.commit()
    await session.refresh(ingest_group)

    return binary_to_uuid(ingest_group.ingest_group_no)
