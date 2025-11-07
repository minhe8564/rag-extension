from __future__ import annotations

from typing import List, Tuple, Optional
import uuid

from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from ..models.ingest_template import (
    IngestGroup,
    ExtractionGroup,
    EmbeddingGroup,
    uuid_to_binary,
    binary_to_uuid
)
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
    total_count_window = func.count().over().label('total_count')

    # 서브쿼리: 필터링과 정렬을 적용한 기본 쿼리
    subquery = select(
        IngestGroup.ingest_group_no,
        IngestGroup.name,
        IngestGroup.is_default,
        IngestGroup.chunking_strategy_no,
        IngestGroup.chunking_parameter,
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

    # 최종 쿼리: IngestGroup 객체로 조회하면서 관계를 eager loading
    query = (
        select(IngestGroup, subquery.c.total_count)
        .join(subquery, IngestGroup.ingest_group_no == subquery.c.ingest_group_no)
        .options(
            selectinload(IngestGroup.chunking_strategy),
            selectinload(IngestGroup.extraction_groups).selectinload(ExtractionGroup.extraction_strategy),
            selectinload(IngestGroup.embedding_groups).selectinload(EmbeddingGroup.embedding_strategy)
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


async def verify_strategy_with_type(
    session: AsyncSession,
    strategy_no: str,
    expected_type: str,
) -> Strategy:
    """
    전략 존재 여부 및 전략 유형 검증

    세분화된 전략 유형을 지원합니다:
    - extraction: extraction-pdf, extraction-docx, extraction-txt, extraction-xlsx
    - embedding: embedding-dense, embedding-spare

    Args:
        session: 데이터베이스 세션
        strategy_no: 전략 ID (UUID 문자열)
        expected_type: 기대되는 전략 유형 이름 (extraction, chunking, embedding 등)

    Returns:
        Strategy 객체

    Raises:
        HTTPException: 전략이 존재하지 않거나 유형이 일치하지 않는 경우
    """
    try:
        strategy_binary = uuid_to_binary(strategy_no)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"유효하지 않은 {expected_type} 전략 ID입니다."
        )

    # Strategy와 StrategyType을 함께 조회
    query = (
        select(Strategy)
        .options(selectinload(Strategy.strategy_type))
        .where(Strategy.strategy_no == strategy_binary)
    )
    result = await session.execute(query)
    strategy = result.scalar_one_or_none()

    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{expected_type} 전략을 찾을 수 없습니다: {strategy_no}"
        )

    # 전략 유형 검증 (세분화된 타입 지원)
    # extraction -> extraction-pdf, extraction-docx 등을 허용
    # embedding -> embedding-dense, embedding-spare 등을 허용
    if strategy.strategy_type:
        actual_type = strategy.strategy_type.name
        # prefix 매칭: extraction-pdf는 extraction으로 시작하므로 통과
        if not actual_type.startswith(expected_type):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"전략 유형이 일치하지 않습니다. 기대: {expected_type}, 실제: {actual_type}"
            )

    return strategy


async def create_ingest_template(
    session: AsyncSession,
    name: str,
    is_default: bool,
    extractions: List[dict],  # [{"no": "uuid", "name": "name", "parameters": {}}]
    chunking_no: str,
    chunking_parameters: dict,
    embeddings: List[dict],   # [{"no": "uuid", "name": "name", "parameters": {}}]
) -> str:
    """
    Ingest 템플릿 생성

    Args:
        session: 데이터베이스 세션
        name: 템플릿 이름
        is_default: 기본 템플릿 여부
        extractions: 추출 전략 리스트 [{"no": str, "name": str, "parameters": dict}]
        chunking_no: 청킹 전략 ID
        chunking_parameters: 청킹 전략 파라미터
        embeddings: 임베딩 전략 리스트 [{"no": str, "name": str, "parameters": dict}]

    Returns:
        생성된 Ingest 템플릿 ID (UUID 문자열)

    Raises:
        HTTPException: 전략을 찾을 수 없거나 유형이 일치하지 않는 경우
    """
    # 청킹 전략 검증
    chunking_strategy = await verify_strategy_with_type(session, chunking_no, "chunking")

    # 추출 전략들 검증
    for ext in extractions:
        await verify_strategy_with_type(session, ext["no"], "extraction")

    # 임베딩 전략들 검증
    for emb in embeddings:
        await verify_strategy_with_type(session, emb["no"], "embedding")

    # 기본 템플릿 설정 시 기존 기본 템플릿 해제
    if is_default:
        await session.execute(
            update(IngestGroup)
            .where(IngestGroup.is_default == True)
            .values(is_default=False)
        )

    # Ingest 그룹 생성
    ingest_group = IngestGroup(
        name=name,
        is_default=is_default,
        chunking_strategy_no=uuid_to_binary(chunking_no),
        chunking_parameter=chunking_parameters or {},
    )

    session.add(ingest_group)
    await session.flush()  # ingest_group_no 생성

    # ExtractionGroup 생성
    for ext in extractions:
        extraction_group = ExtractionGroup(
            ingest_group_no=ingest_group.ingest_group_no,
            name=ext.get("name", "추출 전략"),
            extraction_strategy_no=uuid_to_binary(ext["no"]),
            extraction_parameter=ext.get("parameters", {}),
        )
        session.add(extraction_group)

    # EmbeddingGroup 생성
    for emb in embeddings:
        embedding_group = EmbeddingGroup(
            ingest_group_no=ingest_group.ingest_group_no,
            name=emb.get("name", "임베딩 전략"),
            embedding_strategy_no=uuid_to_binary(emb["no"]),
            embedding_parameter=emb.get("parameters", {}),
        )
        session.add(embedding_group)

    await session.commit()
    await session.refresh(ingest_group)

    return binary_to_uuid(ingest_group.ingest_group_no)


async def get_ingest_template_detail(
    session: AsyncSession,
    ingest_no: str,
) -> Optional[IngestGroup]:
    """
    Ingest 템플릿 상세 조회

    Args:
        session: 데이터베이스 세션
        ingest_no: Ingest 템플릿 ID (UUID 문자열)

    Returns:
        IngestGroup 객체

    Raises:
        HTTPException: 템플릿을 찾을 수 없는 경우
    """
    try:
        ingest_binary = uuid_to_binary(ingest_no)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="유효하지 않은 Ingest 템플릿 ID입니다."
        )

    # IngestGroup 조회 with eager loading
    query = (
        select(IngestGroup)
        .where(IngestGroup.ingest_group_no == ingest_binary)
        .options(
            selectinload(IngestGroup.chunking_strategy),
            selectinload(IngestGroup.extraction_groups).selectinload(ExtractionGroup.extraction_strategy),
            selectinload(IngestGroup.embedding_groups).selectinload(EmbeddingGroup.embedding_strategy)
        )
    )

    result = await session.execute(query)
    ingest_group = result.scalar_one_or_none()

    if not ingest_group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="대상을 찾을 수 없습니다."
        )

    return ingest_group


async def update_ingest_template(
    session: AsyncSession,
    ingest_no: str,
    name: str,
    extractions: List[dict],
    chunking_no: str,
    chunking_parameters: dict,
    embeddings: List[dict],
    is_default: bool,
) -> IngestGroup:
    """
    Ingest 템플릿 수정

    Args:
        session: 데이터베이스 세션
        ingest_no: Ingest 템플릿 ID
        name: 템플릿 이름
        extractions: 추출 전략 리스트
        chunking_no: 청킹 전략 ID
        chunking_parameters: 청킹 전략 파라미터
        embeddings: 임베딩 전략 리스트
        is_default: 기본 템플릿 여부

    Returns:
        수정된 IngestGroup 객체

    Raises:
        HTTPException: 템플릿을 찾을 수 없거나 전략을 찾을 수 없거나 유형이 일치하지 않는 경우
    """
    # 기존 템플릿 조회
    try:
        ingest_binary = uuid_to_binary(ingest_no)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="유효하지 않은 Ingest 템플릿 ID입니다."
        )

    query = (
        select(IngestGroup)
        .where(IngestGroup.ingest_group_no == ingest_binary)
        .options(
            selectinload(IngestGroup.extraction_groups),
            selectinload(IngestGroup.embedding_groups)
        )
    )
    result = await session.execute(query)
    ingest_group = result.scalar_one_or_none()

    if not ingest_group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="대상을 찾을 수 없습니다."
        )

    # 전략 검증
    chunking_strategy = await verify_strategy_with_type(session, chunking_no, "chunking")
    for ext in extractions:
        await verify_strategy_with_type(session, ext["no"], "extraction")
    for emb in embeddings:
        await verify_strategy_with_type(session, emb["no"], "embedding")

    # 기본 템플릿 처리
    if is_default:
        await session.execute(
            update(IngestGroup)
            .where(
                IngestGroup.is_default.is_(True),
                IngestGroup.ingest_group_no != ingest_binary,
            )
            .values(is_default=False)
        )

    # IngestGroup 기본 정보 업데이트
    ingest_group.name = name
    ingest_group.chunking_strategy_no = uuid_to_binary(chunking_no)
    ingest_group.chunking_parameter = chunking_parameters or {}
    ingest_group.is_default = is_default

    # 기존 ExtractionGroup 삭제
    for existing_ext in ingest_group.extraction_groups:
        await session.delete(existing_ext)

    # 기존 EmbeddingGroup 삭제
    for existing_emb in ingest_group.embedding_groups:
        await session.delete(existing_emb)

    await session.flush()

    # 새로운 ExtractionGroup 생성
    for ext in extractions:
        extraction_group = ExtractionGroup(
            ingest_group_no=ingest_group.ingest_group_no,
            name=ext.get("name", "추출 전략"),
            extraction_strategy_no=uuid_to_binary(ext["no"]),
            extraction_parameter=ext.get("parameters", {}),
        )
        session.add(extraction_group)

    # 새로운 EmbeddingGroup 생성
    for emb in embeddings:
        embedding_group = EmbeddingGroup(
            ingest_group_no=ingest_group.ingest_group_no,
            name=emb.get("name", "임베딩 전략"),
            embedding_strategy_no=uuid_to_binary(emb["no"]),
            embedding_parameter=emb.get("parameters", {}),
        )
        session.add(embedding_group)

    await session.commit()

    # 관계 데이터와 함께 다시 조회
    query = (
        select(IngestGroup)
        .where(IngestGroup.ingest_group_no == ingest_binary)
        .options(
            selectinload(IngestGroup.chunking_strategy),
            selectinload(IngestGroup.extraction_groups).selectinload(ExtractionGroup.extraction_strategy),
            selectinload(IngestGroup.embedding_groups).selectinload(EmbeddingGroup.embedding_strategy)
        )
    )
    result = await session.execute(query)
    updated_ingest_group = result.scalar_one()

    return updated_ingest_group


async def delete_ingest_template(
    session: AsyncSession,
    ingest_no: str,
) -> None:
    """
    Ingest 템플릿 삭제

    Args:
        session: 데이터베이스 세션
        ingest_no: Ingest 템플릿 ID

    Raises:
        HTTPException: 템플릿을 찾을 수 없는 경우
    """
    # 템플릿 조회
    try:
        ingest_binary = uuid_to_binary(ingest_no)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="유효하지 않은 Ingest 템플릿 ID입니다."
        )

    query = select(IngestGroup).where(IngestGroup.ingest_group_no == ingest_binary)
    result = await session.execute(query)
    ingest_group = result.scalar_one_or_none()

    if not ingest_group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="대상을 찾을 수 없습니다."
        )

    # 템플릿 삭제
    await session.delete(ingest_group)
    await session.commit()
