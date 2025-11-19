from __future__ import annotations

from typing import Optional, Tuple, List, Dict, Any
import uuid
from copy import deepcopy

from sqlalchemy import select, func, update
from sqlalchemy.orm import noload, selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from ..models.query_template import QueryGroup, uuid_to_binary, binary_to_uuid
from ..models.strategy import Strategy
from ..schemas.query import QueryTemplatePartialUpdateRequest


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


async def get_default_query_template(
    session: AsyncSession,
) -> Optional[QueryGroup]:
    """
    is_default=1인 Query 템플릿 조회

    Args:
        session: 데이터베이스 세션

    Returns:
        QueryGroup 객체 또는 None (기본 템플릿이 없는 경우)
    """
    query = (
        select(QueryGroup)
        .where(QueryGroup.is_default.is_(True))
        .options(
            selectinload(QueryGroup.transformation_strategy),
            selectinload(QueryGroup.retrieval_strategy),
            selectinload(QueryGroup.reranking_strategy),
            selectinload(QueryGroup.system_prompting_strategy),
            selectinload(QueryGroup.user_prompting_strategy),
            selectinload(QueryGroup.generation_strategy),
        )
        .limit(1)
    )
    result = await session.execute(query)
    return result.scalar_one_or_none()


async def get_default_strategy_by_type(
    session: AsyncSession,
    strategy_type: str,
) -> Optional[Strategy]:
    """
    is_default=1인 Query 템플릿에서 사용하는 전략을 기본 전략으로 조회

    Args:
        session: 데이터베이스 세션
        strategy_type: 전략 타입 ("transformation", "retrieval", "reranking", "systemPrompt", "userPrompt", "generation")

    Returns:
        Strategy 객체 또는 None (기본 템플릿이 없거나 해당 전략이 없는 경우)
    """
    default_template = await get_default_query_template(session)
    if not default_template:
        return None

    # 전략 타입에 따라 기본 템플릿에서 사용하는 전략 반환
    if strategy_type == "transformation":
        return default_template.transformation_strategy
    elif strategy_type == "retrieval":
        return default_template.retrieval_strategy
    elif strategy_type == "reranking":
        return default_template.reranking_strategy
    elif strategy_type == "systemPrompt":
        return default_template.system_prompting_strategy
    elif strategy_type == "userPrompt":
        return default_template.user_prompting_strategy
    elif strategy_type == "generation":
        return default_template.generation_strategy
    else:
        return None


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


async def create_query_template(
    session: AsyncSession,
    name: str,
    transformation_no: Optional[str],
    transformation_parameters: dict,
    retrieval_no: Optional[str],
    retrieval_parameters: dict,
    reranking_no: Optional[str],
    reranking_parameters: dict,
    system_prompt_no: Optional[str],
    system_prompt_parameters: dict,
    user_prompt_no: Optional[str],
    user_prompt_parameters: dict,
    generation_no: Optional[str],
    generation_parameters: dict,
    is_default: bool = False,
) -> str:
    """
    Query 템플릿 생성

    Args:
        session: 데이터베이스 세션
        name: 템플릿 이름
        transformation_no: 변환 전략 ID (없으면 기본 전략 사용)
        transformation_parameters: 변환 전략 파라미터
        retrieval_no: 검색 전략 ID (없으면 기본 전략 사용)
        retrieval_parameters: 검색 전략 파라미터
        reranking_no: 재순위화 전략 ID (없으면 기본 전략 사용)
        reranking_parameters: 재순위화 전략 파라미터
        system_prompt_no: 시스템 프롬프트 전략 ID (없으면 기본 전략 사용)
        system_prompt_parameters: 시스템 프롬프트 전략 파라미터
        user_prompt_no: 사용자 프롬프트 전략 ID (없으면 기본 전략 사용)
        user_prompt_parameters: 사용자 프롬프트 전략 파라미터
        generation_no: 생성 전략 ID (없으면 기본 전략 사용)
        generation_parameters: 생성 전략 파라미터

    Returns:
        생성된 Query 템플릿 ID (UUID 문자열)

    Raises:
        HTTPException: 전략을 찾을 수 없는 경우
    """
    # 변환 전략 확인 또는 기본 전략 가져오기
    if transformation_no:
        transformation_strategy = await verify_strategy_exists(session, transformation_no)
        if not transformation_strategy:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"변환 전략을 찾을 수 없습니다: {transformation_no}"
            )
    else:
        transformation_strategy = await get_default_strategy_by_type(session, "transformation")
        if not transformation_strategy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="기본 Query 템플릿 또는 기본 변환 전략을 찾을 수 없습니다."
            )
        transformation_no = binary_to_uuid(transformation_strategy.strategy_no)

    # 검색 전략 확인 또는 기본 전략 가져오기
    if retrieval_no:
        retrieval_strategy = await verify_strategy_exists(session, retrieval_no)
        if not retrieval_strategy:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"검색 전략을 찾을 수 없습니다: {retrieval_no}"
            )
    else:
        retrieval_strategy = await get_default_strategy_by_type(session, "retrieval")
        if not retrieval_strategy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="기본 Query 템플릿 또는 기본 검색 전략을 찾을 수 없습니다."
            )
        retrieval_no = binary_to_uuid(retrieval_strategy.strategy_no)

    # 재순위화 전략 확인 또는 기본 전략 가져오기
    if reranking_no:
        reranking_strategy = await verify_strategy_exists(session, reranking_no)
        if not reranking_strategy:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"재순위화 전략을 찾을 수 없습니다: {reranking_no}"
            )
    else:
        reranking_strategy = await get_default_strategy_by_type(session, "reranking")
        if not reranking_strategy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="기본 Query 템플릿 또는 기본 재순위화 전략을 찾을 수 없습니다."
            )
        reranking_no = binary_to_uuid(reranking_strategy.strategy_no)

    # 시스템 프롬프트 전략 확인 또는 기본 전략 가져오기
    if system_prompt_no:
        system_prompt_strategy = await verify_strategy_exists(session, system_prompt_no)
        if not system_prompt_strategy:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"시스템 프롬프트 전략을 찾을 수 없습니다: {system_prompt_no}"
            )
    else:
        system_prompt_strategy = await get_default_strategy_by_type(session, "systemPrompt")
        if not system_prompt_strategy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="기본 Query 템플릿 또는 기본 시스템 프롬프트 전략을 찾을 수 없습니다."
            )
        system_prompt_no = binary_to_uuid(system_prompt_strategy.strategy_no)

    # 사용자 프롬프트 전략 확인 또는 기본 전략 가져오기
    if user_prompt_no:
        user_prompt_strategy = await verify_strategy_exists(session, user_prompt_no)
        if not user_prompt_strategy:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"사용자 프롬프트 전략을 찾을 수 없습니다: {user_prompt_no}"
            )
    else:
        user_prompt_strategy = await get_default_strategy_by_type(session, "userPrompt")
        if not user_prompt_strategy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="기본 Query 템플릿 또는 기본 사용자 프롬프트 전략을 찾을 수 없습니다."
            )
        user_prompt_no = binary_to_uuid(user_prompt_strategy.strategy_no)

    # 생성 전략 확인 또는 기본 전략 가져오기
    if generation_no:
        generation_strategy = await verify_strategy_exists(session, generation_no)
        if not generation_strategy:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"생성 전략을 찾을 수 없습니다: {generation_no}"
            )
    else:
        generation_strategy = await get_default_strategy_by_type(session, "generation")
        if not generation_strategy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="기본 Query 템플릿 또는 기본 생성 전략을 찾을 수 없습니다."
            )
        generation_no = binary_to_uuid(generation_strategy.strategy_no)

    # 기존 기본 템플릿 해제
    if is_default:
        await session.execute(
            update(QueryGroup)
            .where(QueryGroup.is_default.is_(True))
            .values(is_default=False)
        )

    # Query 그룹 생성
    query_group = QueryGroup(
        name=name,
        is_default=is_default,
        transformation_strategy_no=uuid_to_binary(transformation_no),
        retrieval_strategy_no=uuid_to_binary(retrieval_no),
        reranking_strategy_no=uuid_to_binary(reranking_no),
        system_prompting_strategy_no=uuid_to_binary(system_prompt_no),
        user_prompting_strategy_no=uuid_to_binary(user_prompt_no),
        generation_strategy_no=uuid_to_binary(generation_no),
        transformation_parameter=build_strategy_parameters(
            transformation_strategy, transformation_parameters
        ),
        retrieval_parameter=build_strategy_parameters(
            retrieval_strategy, retrieval_parameters
        ),
        reranking_parameter=build_strategy_parameters(
            reranking_strategy, reranking_parameters
        ),
        system_prompting_parameter=build_strategy_parameters(
            system_prompt_strategy, system_prompt_parameters
        ),
        user_prompting_parameter=build_strategy_parameters(
            user_prompt_strategy, user_prompt_parameters
        ),
        generation_parameter=build_strategy_parameters(
            generation_strategy, generation_parameters
        ),
    )

    session.add(query_group)
    await session.commit()
    await session.refresh(query_group)

    return binary_to_uuid(query_group.query_group_no)


async def list_query_templates(
    session: AsyncSession,
    page_num: int = 1,
    page_size: int = 20,
) -> Tuple[List[QueryGroup], int]:
    """
    Query 템플릿 목록 조회 (윈도우 함수를 사용한 최적화 버전)

    Args:
        session: 데이터베이스 세션
        page_num: 페이지 번호
        page_size: 페이지 크기

    Returns:
        (Query 템플릿 목록, 전체 항목 수)
    """
    # 윈도우 함수를 사용한 전체 카운트 계산
    total_count_window = func.count(QueryGroup.query_group_no).over().label('total_count')

    # 서브쿼리: 필터링과 정렬을 적용한 기본 쿼리
    subquery = select(
        QueryGroup.query_group_no,
        QueryGroup.name,
        QueryGroup.is_default,
        total_count_window
    )

    # 정렬 (이름 오름차 순)
    subquery = subquery.order_by(QueryGroup.name.asc())

    # 페이지네이션 적용
    offset = (page_num - 1) * page_size
    subquery = subquery.offset(offset).limit(page_size)

    # 서브쿼리를 서브쿼리로 래핑
    subquery = subquery.subquery()

    # 최종 쿼리: QueryGroup 객체로 조회 (관계 로딩 비활성화)
    query = (
        select(QueryGroup, subquery.c.total_count)
        .join(subquery, QueryGroup.query_group_no == subquery.c.query_group_no)
        .options(
            noload(QueryGroup.transformation_strategy),
            noload(QueryGroup.retrieval_strategy),
            noload(QueryGroup.reranking_strategy),
            noload(QueryGroup.system_prompting_strategy),
            noload(QueryGroup.user_prompting_strategy),
            noload(QueryGroup.generation_strategy),
        )
    )

    # 쿼리 실행
    result = await session.execute(query)
    rows = result.all()

    # 결과 분리
    if not rows:
        return [], 0

    query_groups = [row[0] for row in rows]
    total_items = rows[0][1] if rows else 0

    return query_groups, total_items


async def get_query_template(
    session: AsyncSession,
    query_no: str,
) -> Optional[QueryGroup]:
    """
    Query 템플릿 상세 조회

    Args:
        session: 데이터베이스 세션
        query_no: Query 템플릿 ID (UUID 문자열)

    Returns:
        QueryGroup 객체 또는 None

    Raises:
        HTTPException: UUID 형식이 잘못되었거나 템플릿을 찾을 수 없는 경우
    """
    # UUID 변환
    try:
        query_binary = uuid_to_binary(query_no)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="올바르지 않은 Query 템플릿 ID 형식입니다."
        )

    # Query 템플릿 조회 (전략들과 함께 로딩)
    query = (
        select(QueryGroup)
        .where(QueryGroup.query_group_no == query_binary)
        .options(
            selectinload(QueryGroup.transformation_strategy),
            selectinload(QueryGroup.retrieval_strategy),
            selectinload(QueryGroup.reranking_strategy),
            selectinload(QueryGroup.system_prompting_strategy),
            selectinload(QueryGroup.user_prompting_strategy),
            selectinload(QueryGroup.generation_strategy),
        )
    )

    result = await session.execute(query)
    query_group = result.scalar_one_or_none()

    if not query_group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="대상을 찾을 수 없습니다."
        )

    return query_group


async def partial_update_query_template(
    session: AsyncSession,
    query_no: str,
    name: Optional[str] = None,
    transformation_no: Optional[str] = None,
    transformation_parameters: Optional[dict] = None,
    retrieval_no: Optional[str] = None,
    retrieval_parameters: Optional[dict] = None,
    reranking_no: Optional[str] = None,
    reranking_parameters: Optional[dict] = None,
    system_prompt_no: Optional[str] = None,
    system_prompt_parameters: Optional[dict] = None,
    user_prompt_no: Optional[str] = None,
    user_prompt_parameters: Optional[dict] = None,
    generation_no: Optional[str] = None,
    generation_parameters: Optional[dict] = None,
    is_default: Optional[bool] = None,
) -> QueryGroup:
    """
    Query 템플릿 부분 수정

    전달된 필드만 업데이트합니다.
    """
    try:
        query_binary = uuid_to_binary(query_no)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="올바르지 않은 Query 템플릿 ID 형식입니다."
        )

    query = select(QueryGroup).where(QueryGroup.query_group_no == query_binary)
    result = await session.execute(query)
    query_group = result.scalar_one_or_none()

    if not query_group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="대상을 찾을 수 없습니다."
        )

    if name is not None:
        query_group.name = name

    if transformation_no is not None:
        transformation_strategy = await verify_strategy_exists(session, transformation_no)
        if not transformation_strategy:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"변환 전략을 찾을 수 없습니다: {transformation_no}"
            )
        transformation_binary = uuid_to_binary(transformation_no)
        same_strategy = query_group.transformation_strategy_no == transformation_binary
        existing_params = (
            query_group.transformation_parameter if same_strategy else None
        )
        query_group.transformation_strategy_no = transformation_binary
        query_group.transformation_parameter = build_strategy_parameters(
            transformation_strategy,
            transformation_parameters,
            existing=existing_params,
        )

    if retrieval_no is not None:
        retrieval_strategy = await verify_strategy_exists(session, retrieval_no)
        if not retrieval_strategy:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"검색 전략을 찾을 수 없습니다: {retrieval_no}"
            )
        retrieval_binary = uuid_to_binary(retrieval_no)
        same_strategy = query_group.retrieval_strategy_no == retrieval_binary
        existing_params = query_group.retrieval_parameter if same_strategy else None
        query_group.retrieval_strategy_no = retrieval_binary
        query_group.retrieval_parameter = build_strategy_parameters(
            retrieval_strategy,
            retrieval_parameters,
            existing=existing_params,
        )

    if reranking_no is not None:
        reranking_strategy = await verify_strategy_exists(session, reranking_no)
        if not reranking_strategy:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"재순위화 전략을 찾을 수 없습니다: {reranking_no}"
            )
        reranking_binary = uuid_to_binary(reranking_no)
        same_strategy = query_group.reranking_strategy_no == reranking_binary
        existing_params = query_group.reranking_parameter if same_strategy else None
        query_group.reranking_strategy_no = reranking_binary
        query_group.reranking_parameter = build_strategy_parameters(
            reranking_strategy,
            reranking_parameters,
            existing=existing_params,
        )

    if system_prompt_no is not None:
        system_prompt_strategy = await verify_strategy_exists(session, system_prompt_no)
        if not system_prompt_strategy:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"시스템 프롬프트 전략을 찾을 수 없습니다: {system_prompt_no}"
            )
        system_prompt_binary = uuid_to_binary(system_prompt_no)
        same_strategy = query_group.system_prompting_strategy_no == system_prompt_binary
        existing_params = (
            query_group.system_prompting_parameter if same_strategy else None
        )
        query_group.system_prompting_strategy_no = system_prompt_binary
        query_group.system_prompting_parameter = build_strategy_parameters(
            system_prompt_strategy,
            system_prompt_parameters,
            existing=existing_params,
        )

    if user_prompt_no is not None:
        user_prompt_strategy = await verify_strategy_exists(session, user_prompt_no)
        if not user_prompt_strategy:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"사용자 프롬프트 전략을 찾을 수 없습니다: {user_prompt_no}"
            )
        user_prompt_binary = uuid_to_binary(user_prompt_no)
        same_strategy = query_group.user_prompting_strategy_no == user_prompt_binary
        existing_params = (
            query_group.user_prompting_parameter if same_strategy else None
        )
        query_group.user_prompting_strategy_no = user_prompt_binary
        query_group.user_prompting_parameter = build_strategy_parameters(
            user_prompt_strategy,
            user_prompt_parameters,
            existing=existing_params,
        )

    if generation_no is not None:
        generation_strategy = await verify_strategy_exists(session, generation_no)
        if not generation_strategy:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"생성 전략을 찾을 수 없습니다: {generation_no}"
            )
        generation_binary = uuid_to_binary(generation_no)
        same_strategy = query_group.generation_strategy_no == generation_binary
        existing_params = query_group.generation_parameter if same_strategy else None
        query_group.generation_strategy_no = generation_binary
        query_group.generation_parameter = build_strategy_parameters(
            generation_strategy,
            generation_parameters,
            existing=existing_params,
        )

    if is_default is True:
        await session.execute(
            update(QueryGroup)
            .where(
                QueryGroup.is_default.is_(True),
                QueryGroup.query_group_no != query_binary,
            )
            .values(is_default=False)
        )
        query_group.is_default = True
    elif is_default is False:
        query_group.is_default = False

    await session.commit()
    await session.refresh(query_group)

    query = (
        select(QueryGroup)
        .where(QueryGroup.query_group_no == query_binary)
        .options(
            selectinload(QueryGroup.transformation_strategy),
            selectinload(QueryGroup.retrieval_strategy),
            selectinload(QueryGroup.reranking_strategy),
            selectinload(QueryGroup.system_prompting_strategy),
            selectinload(QueryGroup.user_prompting_strategy),
            selectinload(QueryGroup.generation_strategy),
        )
    )
    result = await session.execute(query)
    updated_query_group = result.scalar_one()

    return updated_query_group

async def delete_query_template(
    session: AsyncSession,
    query_no: str,
) -> None:
    """
    Query 템플릿 삭제

    Args:
        session: 데이터베이스 세션
        query_no: Query 템플릿 ID (UUID 문자열)

    Raises:
        HTTPException: UUID 형식 오류 또는 템플릿을 찾을 수 없는 경우
    """
    # UUID 변환
    try:
        query_binary = uuid_to_binary(query_no)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="올바르지 않은 Query 템플릿 ID 형식입니다."
        )

    # Query 템플릿 조회
    query = select(QueryGroup).where(QueryGroup.query_group_no == query_binary)
    result = await session.execute(query)
    query_group = result.scalar_one_or_none()

    if not query_group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="대상을 찾을 수 없습니다."
        )

    # 기본 템플릿은 삭제할 수 없음
    if query_group.is_default:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="기본 템플릿은 삭제할 수 없습니다."
        )

    # Query 템플릿 삭제
    await session.delete(query_group)
    await session.commit()
