from __future__ import annotations

from typing import List, Tuple, Optional, Dict, Any
from copy import deepcopy

from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, noload
from fastapi import HTTPException, status

from ..models.ingest_template import (
    IngestGroup,
    ExtractionGroup,
    EmbeddingGroup,
    uuid_to_binary,
    binary_to_uuid,
)
from ..models.strategy import Strategy


async def list_ingest_groups(
    session: AsyncSession,
    page_num: int = 1,
    page_size: int = 20,
) -> Tuple[List[IngestGroup], int]:
    """
    Ingest 그룹 목록 조회 (윈도우 함수를 사용한 최적화 버전)

    단일 쿼리로 데이터와 전체 카운트를 동시에 조회하여 성능을 개선하고,
    필터 조건의 동기화 문제를 방지합니다.

    Args:
        session: 데이터베이스 세션
        page_num: 페이지 번호
        page_size: 페이지 크기

    Returns:
        (Ingest 그룹 목록, 전체 항목 수)
    """
    # 윈도우 함수를 사용한 전체 카운트 계산
    # count() over()는 필터링된 결과 전체의 개수를 각 행에 포함시킴
    total_count_window = func.count(IngestGroup.ingest_group_no).over().label('total_count')

    # 서브쿼리: 필터링과 정렬을 적용한 기본 쿼리
    subquery = select(
        IngestGroup.ingest_group_no,
        IngestGroup.name,
        IngestGroup.is_default,
        total_count_window
    ).order_by(IngestGroup.name.asc())

    # 페이지네이션 적용
    offset = (page_num - 1) * page_size
    subquery = subquery.offset(offset).limit(page_size)

    # 서브쿼리를 서브쿼리로 래핑
    subquery = subquery.subquery()

    # 최종 쿼리: IngestGroup 객체로 조회하면서 불필요한 관계 로딩 비활성화
    query = (
        select(IngestGroup, subquery.c.total_count)
        .join(subquery, IngestGroup.ingest_group_no == subquery.c.ingest_group_no)
        .options(
            noload(IngestGroup.chunking_strategy),
            noload(IngestGroup.extraction_groups),
            noload(IngestGroup.embedding_groups),
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


def _apply_allowed_overrides(
    allowed: Dict[str, Any],
    target: Dict[str, Any],
    overrides: Dict[str, Any],
) -> None:
    for key, value in overrides.items():
        if key not in allowed:
            continue
        allowed_value = allowed[key]
        if isinstance(allowed_value, dict) and isinstance(value, dict):
            target_value = target.get(key)
            if not isinstance(target_value, dict):
                target_value = deepcopy(allowed_value)
            else:
                target_value = deepcopy(target_value)
            _apply_allowed_overrides(allowed_value, target_value, value)
            target[key] = target_value
        else:
            target[key] = value


def build_strategy_parameters(
    strategy: Strategy,
    overrides: Optional[Dict[str, Any]] = None,
    existing: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    allowed = strategy.parameter or {}
    base = deepcopy(allowed)

    if existing:
        _apply_allowed_overrides(allowed, base, existing)

    if overrides:
        _apply_allowed_overrides(allowed, base, overrides)

    return base


async def create_ingest_template(
    session: AsyncSession,
    name: str,
    is_default: bool,
    extractions: List[Dict[str, Any]],
    chunking: Dict[str, Any],
    dense_embeddings: Optional[List[Dict[str, Any]]] = None,
    sparse_embedding: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Ingest 템플릿 생성

    Args:
        session: 데이터베이스 세션
        name: 템플릿 이름
        is_default: 기본 템플릿 여부
        extractions: 추출 전략 목록
        chunking: 청킹 전략 정보
        dense_embeddings: 밀집 임베딩 전략 목록
        sparse_embedding: 희소(대표) 임베딩 전략 정보

    Returns:
        생성된 Ingest 템플릿 ID (UUID 문자열)

    Raises:
        HTTPException: 전략을 찾을 수 없는 경우
    """
    if not extractions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="추출 전략은 최소 1개 이상이어야 합니다."
        )

    if sparse_embedding is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="sparseEmbedding 전략 정보가 필요합니다."
        )

    if not chunking:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="chunking 전략 정보가 필요합니다."
        )

    dense_embeddings = dense_embeddings or []

    # 전략 존재 여부 확인
    chunking_no = chunking.get("no")
    if not chunking_no:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="chunking 전략 ID가 누락되었습니다."
        )
    chunking_strategy = await verify_strategy_exists(session, chunking_no)
    if not chunking_strategy:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"청킹 전략을 찾을 수 없습니다: {chunking_no}"
        )

    sparse_no = sparse_embedding.get("no")
    if not sparse_no:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="sparseEmbedding 전략 ID가 누락되었습니다."
        )

    sparse_strategy = await verify_strategy_exists(session, sparse_no)
    if not sparse_strategy:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"희소 임베딩 전략을 찾을 수 없습니다: {sparse_no}"
        )

    if (sparse_strategy.code or "").upper() != "EMB_SPARSE":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="희소 임베딩 전략은 STRATEGY.CODE가 EMB_SPARSE인 항목만 사용할 수 있습니다."
        )

    sparse_parameters = build_strategy_parameters(
        sparse_strategy,
        sparse_embedding.get("parameters"),
    )

    # 기본 템플릿 설정 시 기존 기본 템플릿 해제
    if is_default:
        await session.execute(
            update(IngestGroup)
            .where(IngestGroup.is_default.is_(True))
            .values(is_default=False)
        )

    # Ingest 그룹 생성
    ingest_group = IngestGroup(
        name=name,
        is_default=is_default,
        chunking_strategy_no=chunking_strategy.strategy_no,
        chunking_parameter=build_strategy_parameters(
            chunking_strategy, chunking.get("parameters")
        ),
        sparse_embedding_strategy_no=sparse_strategy.strategy_no,
        sparse_embedding_parameter=sparse_parameters,
    )

    session.add(ingest_group)

    # 추출 전략 그룹 생성
    for extraction in extractions:
        extraction_no = extraction.get("no")
        if not extraction_no:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="추출 전략 ID가 누락되었습니다."
            )
        extraction_strategy = await verify_strategy_exists(session, extraction_no)
        if not extraction_strategy:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"추출 전략을 찾을 수 없습니다: {extraction_no}"
            )

        extraction_group = ExtractionGroup(
            name=extraction_strategy.name,
            extraction_strategy_no=extraction_strategy.strategy_no,
            extraction_parameter=build_strategy_parameters(
                extraction_strategy,
                extraction.get("parameters"),
            ),
        )
        extraction_group.ingest_group = ingest_group
        session.add(extraction_group)

    # 임베딩 전략 그룹 생성 (dense only)
    for embedding in dense_embeddings:
        embedding_no = embedding.get("no")
        if not embedding_no:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="임베딩 전략 ID가 누락되었습니다."
            )
        embedding_strategy = await verify_strategy_exists(session, embedding_no)
        if not embedding_strategy:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"임베딩 전략을 찾을 수 없습니다: {embedding_no}"
            )

        if (embedding_strategy.code or "").upper() != "EMB_DENSE":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="밀집 임베딩 전략은 STRATEGY.CODE가 EMB_DENSE인 항목만 사용할 수 있습니다."
            )

        embedding_group = EmbeddingGroup(
            name=embedding_strategy.name,
            embedding_strategy_no=embedding_strategy.strategy_no,
            embedding_parameter=build_strategy_parameters(
                embedding_strategy,
                embedding.get("parameters"),
            ),
        )
        embedding_group.ingest_group = ingest_group
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
        IngestGroup 객체 또는 None

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
            selectinload(IngestGroup.sparse_embedding_strategy),
            selectinload(IngestGroup.extraction_groups).selectinload(ExtractionGroup.extraction_strategy),
            selectinload(IngestGroup.embedding_groups).selectinload(EmbeddingGroup.embedding_strategy),
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
    extractions: List[Dict[str, Any]],
    chunking: Dict[str, Any],
    dense_embeddings: Optional[List[Dict[str, Any]]] = None,
    sparse_embedding: Optional[Dict[str, Any]] = None,
    is_default: bool = False,
) -> IngestGroup:
    """
    Ingest 템플릿 수정

    Args:
        session: 데이터베이스 세션
        ingest_no: Ingest 템플릿 ID
        name: 템플릿 이름
        extractions: 추출 전략 목록
        chunking: 청킹 전략 정보
        dense_embeddings: 밀집 임베딩 전략 목록
        sparse_embedding: 희소(대표) 임베딩 전략 정보

    Returns:
        수정된 IngestGroup 객체

    Raises:
        HTTPException: 템플릿을 찾을 수 없거나 전략을 찾을 수 없는 경우
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
            selectinload(IngestGroup.chunking_strategy),
            selectinload(IngestGroup.extraction_groups).selectinload(ExtractionGroup.extraction_strategy),
            selectinload(IngestGroup.embedding_groups).selectinload(EmbeddingGroup.embedding_strategy),
        )
    )
    result = await session.execute(query)
    ingest_group = result.scalar_one_or_none()

    if not ingest_group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="대상을 찾을 수 없습니다."
        )

    if not extractions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="추출 전략은 최소 1개 이상이어야 합니다."
        )

    if sparse_embedding is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="sparseEmbedding 전략 정보가 필요합니다."
        )

    if not chunking:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="chunking 전략 정보가 필요합니다."
        )

    dense_embeddings = dense_embeddings or []

    # 청킹 전략 검증
    chunking_no = chunking.get("no")
    if not chunking_no:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="chunking 전략 ID가 누락되었습니다."
        )
    chunking_strategy = await verify_strategy_exists(session, chunking_no)
    if not chunking_strategy:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"청킹 전략을 찾을 수 없습니다: {chunking_no}"
        )

    sparse_no = sparse_embedding.get("no")
    if not sparse_no:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="sparseEmbedding 전략 ID가 누락되었습니다."
        )

    sparse_strategy = await verify_strategy_exists(session, sparse_no)
    if not sparse_strategy:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"희소 임베딩 전략을 찾을 수 없습니다: {sparse_no}"
        )

    if (sparse_strategy.code or "").upper() != "EMB_SPARSE":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="희소 임베딩 전략은 STRATEGY.CODE가 EMB_SPARSE인 항목만 사용할 수 있습니다."
        )

    sparse_parameters = build_strategy_parameters(
        sparse_strategy,
        sparse_embedding.get("parameters"),
    )

    # 템플릿 기본 정보 업데이트
    ingest_group.name = name
    ingest_group.chunking_strategy_no = chunking_strategy.strategy_no
    ingest_group.chunking_parameter = build_strategy_parameters(
        chunking_strategy,
        chunking.get("parameters"),
    )
    ingest_group.sparse_embedding_strategy_no = sparse_strategy.strategy_no
    ingest_group.sparse_embedding_parameter = sparse_parameters

    # 추출 전략 동기화
    existing_extraction_groups = list(ingest_group.extraction_groups)

    for idx, extraction in enumerate(extractions):
        extraction_no = extraction.get("no")
        if not extraction_no:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="추출 전략 ID가 누락되었습니다."
            )
        extraction_strategy = await verify_strategy_exists(session, extraction_no)
        if not extraction_strategy:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"추출 전략을 찾을 수 없습니다: {extraction_no}"
            )

        parameters = build_strategy_parameters(
            extraction_strategy,
            extraction.get("parameters"),
        )

        if idx < len(existing_extraction_groups):
            extraction_group = existing_extraction_groups[idx]
            extraction_group.name = extraction_strategy.name
            extraction_group.extraction_strategy_no = extraction_strategy.strategy_no
            extraction_group.extraction_parameter = parameters
        else:
            extraction_group = ExtractionGroup(
                name=extraction_strategy.name,
                extraction_strategy_no=extraction_strategy.strategy_no,
                extraction_parameter=parameters,
            )
            extraction_group.ingest_group = ingest_group
            session.add(extraction_group)

    # 남은 기존 추출 그룹 제거
    for group in existing_extraction_groups[len(extractions):]:
        await session.delete(group)

    # 임베딩 전략 동기화 (dense only)
    existing_embedding_groups = list(ingest_group.embedding_groups)

    for idx, embedding in enumerate(dense_embeddings):
        embedding_no = embedding.get("no")
        if not embedding_no:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="임베딩 전략 ID가 누락되었습니다."
            )
        embedding_strategy = await verify_strategy_exists(session, embedding_no)
        if not embedding_strategy:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"임베딩 전략을 찾을 수 없습니다: {embedding_no}"
            )

        if (embedding_strategy.code or "").upper() != "EMB_DENSE":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="밀집 임베딩 전략은 STRATEGY.CODE가 EMB_DENSE인 항목만 사용할 수 있습니다."
            )

        parameters = build_strategy_parameters(
            embedding_strategy,
            embedding.get("parameters"),
        )

        if idx < len(existing_embedding_groups):
            embedding_group = existing_embedding_groups[idx]
            embedding_group.name = embedding_strategy.name
            embedding_group.embedding_strategy_no = embedding_strategy.strategy_no
            embedding_group.embedding_parameter = parameters
        else:
            embedding_group = EmbeddingGroup(
                name=embedding_strategy.name,
                embedding_strategy_no=embedding_strategy.strategy_no,
                embedding_parameter=parameters,
            )
            embedding_group.ingest_group = ingest_group
            session.add(embedding_group)

    for group in existing_embedding_groups[len(dense_embeddings):]:
        await session.delete(group)

    if is_default:
        await session.execute(
            update(IngestGroup)
            .where(
                IngestGroup.is_default.is_(True),
                IngestGroup.ingest_group_no != ingest_binary,
            )
            .values(is_default=False)
        )
        ingest_group.is_default = True
    else:
        ingest_group.is_default = False

    await session.commit()

    # 관계 데이터와 함께 다시 조회
    query = (
        select(IngestGroup)
        .where(IngestGroup.ingest_group_no == ingest_binary)
        .options(
            selectinload(IngestGroup.chunking_strategy),
            selectinload(IngestGroup.sparse_embedding_strategy),
            selectinload(IngestGroup.extraction_groups).selectinload(ExtractionGroup.extraction_strategy),
            selectinload(IngestGroup.embedding_groups).selectinload(EmbeddingGroup.embedding_strategy),
        )
    )
    result = await session.execute(query)
    updated_ingest_group = result.scalar_one()

    return updated_ingest_group


async def partial_update_ingest_template(
    session: AsyncSession,
    ingest_no: str,
    name: Optional[str] = None,
    extractions: Optional[List[Dict[str, Any]]] = None,
    chunking: Optional[Dict[str, Any]] = None,
    dense_embeddings: Optional[List[Dict[str, Any]]] = None,
    sparse_embedding: Optional[Dict[str, Any]] = None,
    is_default: Optional[bool] = None,
) -> IngestGroup:
    """
    Ingest 템플릿 부분 수정
    전달된 필드만 업데이트합니다.
    """
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
            selectinload(IngestGroup.chunking_strategy),
            selectinload(IngestGroup.extraction_groups).selectinload(ExtractionGroup.extraction_strategy),
            selectinload(IngestGroup.embedding_groups).selectinload(EmbeddingGroup.embedding_strategy),
        )
    )
    result = await session.execute(query)
    ingest_group = result.scalar_one_or_none()

    if not ingest_group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="대상을 찾을 수 없습니다."
        )

    if name is not None:
        ingest_group.name = name

    if chunking is not None:
        chunking_no = chunking.get("no")
        if not chunking_no:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="chunking 전략 ID가 누락되었습니다."
            )
        chunking_strategy = await verify_strategy_exists(session, chunking_no)
        if not chunking_strategy:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"청킹 전략을 찾을 수 없습니다: {chunking_no}"
            )
        ingest_group.chunking_strategy_no = chunking_strategy.strategy_no
        ingest_group.chunking_parameter = build_strategy_parameters(
            chunking_strategy,
            chunking.get("parameters"),
            existing=ingest_group.chunking_parameter,
        )

    if extractions is not None:
        existing_extraction_groups = list(ingest_group.extraction_groups)

        for idx, extraction in enumerate(extractions):
            extraction_no = extraction.get("no")
            if not extraction_no:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="추출 전략 ID가 누락되었습니다."
                )
            extraction_strategy = await verify_strategy_exists(session, extraction_no)
            if not extraction_strategy:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"추출 전략을 찾을 수 없습니다: {extraction_no}"
                )

            parameters = build_strategy_parameters(
                extraction_strategy,
                extraction.get("parameters"),
                existing=existing_extraction_groups[idx].extraction_parameter if idx < len(existing_extraction_groups) else None,
            )

            if idx < len(existing_extraction_groups):
                extraction_group = existing_extraction_groups[idx]
                extraction_group.name = extraction_strategy.name
                extraction_group.extraction_strategy_no = extraction_strategy.strategy_no
                extraction_group.extraction_parameter = parameters
            else:
                extraction_group = ExtractionGroup(
                    name=extraction_strategy.name,
                    extraction_strategy_no=extraction_strategy.strategy_no,
                    extraction_parameter=parameters,
                )
                extraction_group.ingest_group = ingest_group
                session.add(extraction_group)

        for group in existing_extraction_groups[len(extractions):]:
            await session.delete(group)

    if sparse_embedding is not None:
        sparse_no = sparse_embedding.get("no")
        if not sparse_no:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="sparseEmbedding 전략 ID가 누락되었습니다."
            )
        sparse_strategy = await verify_strategy_exists(session, sparse_no)
        if not sparse_strategy:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"희소 임베딩 전략을 찾을 수 없습니다: {sparse_no}"
            )
        if (sparse_strategy.code or "").upper() != "EMB_SPARSE":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="희소 임베딩 전략은 STRATEGY.CODE가 EMB_SPARSE인 항목만 사용할 수 있습니다."
            )
        ingest_group.sparse_embedding_strategy_no = sparse_strategy.strategy_no
        ingest_group.sparse_embedding_parameter = build_strategy_parameters(
            sparse_strategy,
            sparse_embedding.get("parameters"),
            existing=ingest_group.sparse_embedding_parameter,
        )

    if dense_embeddings is not None:
        dense_embeddings = dense_embeddings or []
        existing_embedding_groups = list(ingest_group.embedding_groups)

        for idx, embedding in enumerate(dense_embeddings):
            embedding_no = embedding.get("no")
            if not embedding_no:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="임베딩 전략 ID가 누락되었습니다."
                )
            embedding_strategy = await verify_strategy_exists(session, embedding_no)
            if not embedding_strategy:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"임베딩 전략을 찾을 수 없습니다: {embedding_no}"
                )

            if (embedding_strategy.code or "").upper() != "EMB_DENSE":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="밀집 임베딩 전략은 STRATEGY.CODE가 EMB_DENSE인 항목만 사용할 수 있습니다."
                )

            existing_params = (
                existing_embedding_groups[idx].embedding_parameter
                if idx < len(existing_embedding_groups)
                else None
            )

            parameters = build_strategy_parameters(
                embedding_strategy,
                embedding.get("parameters"),
                existing=existing_params,
            )

            if idx < len(existing_embedding_groups):
                embedding_group = existing_embedding_groups[idx]
                embedding_group.name = embedding_strategy.name
                embedding_group.embedding_strategy_no = embedding_strategy.strategy_no
                embedding_group.embedding_parameter = parameters
            else:
                embedding_group = EmbeddingGroup(
                    name=embedding_strategy.name,
                    embedding_strategy_no=embedding_strategy.strategy_no,
                    embedding_parameter=parameters,
                )
                embedding_group.ingest_group = ingest_group
                session.add(embedding_group)

        for group in existing_embedding_groups[len(dense_embeddings):]:
            await session.delete(group)

    if is_default is True:
        await session.execute(
            update(IngestGroup)
            .where(
                IngestGroup.is_default.is_(True),
                IngestGroup.ingest_group_no != ingest_binary,
            )
            .values(is_default=False)
        )
        ingest_group.is_default = True
    elif is_default is False:
        ingest_group.is_default = False

    await session.commit()
    await session.refresh(ingest_group)

    query = (
        select(IngestGroup)
        .where(IngestGroup.ingest_group_no == ingest_binary)
        .options(
            selectinload(IngestGroup.chunking_strategy),
            selectinload(IngestGroup.sparse_embedding_strategy),
            selectinload(IngestGroup.extraction_groups).selectinload(ExtractionGroup.extraction_strategy),
            selectinload(IngestGroup.embedding_groups).selectinload(EmbeddingGroup.embedding_strategy),
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
