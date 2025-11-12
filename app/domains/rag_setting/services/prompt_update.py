"""
프롬프트 수정 서비스
"""
from __future__ import annotations

import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from ..models.strategy import Strategy, StrategyType
from ..models.query_template import QueryGroup
from .prompt_create import PROMPT_TYPE_CODE_MAP, get_prompting_strategy_type


async def check_prompt_name_conflict(
    session: AsyncSession,
    name: str,
    exclude_prompt_no: bytes,
    prompt_type: str
) -> bool:
    """
    프롬프트 이름 중복 확인 (자기 자신 제외, 같은 타입 내에서만)

    Args:
        session: 데이터베이스 세션
        name: 프롬프트 이름
        exclude_prompt_no: 제외할 프롬프트 ID (자기 자신)
        prompt_type: 프롬프트 유형 ('system' 또는 'user')

    Returns:
        중복 여부 (True: 중복 존재, False: 중복 없음)
    """
    # 전략 유형 이름 생성
    strategy_type_name = f"prompting-{prompt_type}"

    query = (
        select(Strategy)
        .join(Strategy.strategy_type)
        .where(
            Strategy.name == name,
            Strategy.strategy_no != exclude_prompt_no,
            StrategyType.name.in_(["prompting-system", "prompting-user"])
        )
    )

    result = await session.execute(query)
    existing_strategy = result.scalar_one_or_none()

    return existing_strategy is not None


async def update_prompt(
    session: AsyncSession,
    prompt_no_str: str,
    name: str,
    description: str,
    content: str,
    prompt_type: str | None = None
) -> Strategy:
    """
    프롬프트 수정

    Args:
        session: 데이터베이스 세션
        prompt_no_str: 프롬프트 ID (UUID 문자열)
        name: 새로운 프롬프트명
        description: 새로운 프롬프트 요약 설명 (최대 255자)
        content: 새로운 프롬프트 실제 내용 (제한 없음)

    Returns:
        수정된 Strategy 객체

    Raises:
        HTTPException: 404 - 프롬프트를 찾을 수 없음
        HTTPException: 409 - 중복된 이름 존재
    """
    try:
        # UUID 문자열을 바이너리로 변환
        prompt_no_bytes = uuid.UUID(prompt_no_str).bytes
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="대상을 찾을 수 없습니다."
        )

    # 1. 프롬프트 조회
    query = (
        select(Strategy)
        .join(Strategy.strategy_type)
        .where(
            Strategy.strategy_no == prompt_no_bytes,
            StrategyType.name.in_(["prompting-system", "prompting-user"])
        )
    )

    result = await session.execute(query)
    prompt = result.scalar_one_or_none()

    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="대상을 찾을 수 없습니다."
        )

    # 현재 프롬프트 타입 확인
    existing_type = prompt.parameter.get("type", "system") if prompt.parameter else "system"

    # 2. 이름 중복 확인 (자기 자신 제외, 같은 타입 내에서만)
    if await check_prompt_name_conflict(session, name, prompt_no_bytes, existing_type):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="동일한 이름의 프롬프트가 존재합니다."
        )

    # 3. 프롬프트 수정
    prompt.name = name
    prompt.description = description  # 요약 설명 (최대 255자)

    existing_type = prompt.parameter.get("type", "system") if prompt.parameter else "system"
    target_type = prompt_type or existing_type

    if target_type not in ("system", "user"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="지원하지 않는 프롬프트 유형입니다. (system, user만 허용)",
        )

    if prompt_type and target_type != existing_type:
        strategy_type = await get_prompting_strategy_type(session, target_type)
        prompt.strategy_type_no = strategy_type.strategy_type_no
        prompt.strategy_type = strategy_type

    prompt.code = PROMPT_TYPE_CODE_MAP[target_type]

    prompt.parameter = {
        "content": content,  # 실제 프롬프트 내용 (제한 없음)
        "type": target_type
    }

    await session.execute(
        update(QueryGroup)
        .where(QueryGroup.system_prompting_strategy_no == prompt.strategy_no)
        .values(system_prompting_parameter=prompt.parameter)
    )

    await session.execute(
        update(QueryGroup)
        .where(QueryGroup.user_prompting_strategy_no == prompt.strategy_no)
        .values(user_prompting_parameter=prompt.parameter)
    )

    await session.commit()
    await session.refresh(prompt)

    return prompt
