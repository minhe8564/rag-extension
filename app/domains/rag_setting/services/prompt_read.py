"""
프롬프트 조회 서비스 (목록 + 상세)
"""
from __future__ import annotations

from typing import List, Optional
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.strategy import Strategy, StrategyType


async def list_prompts(
    session: AsyncSession,
    prompt_type: str | None = None,
) -> List[Strategy]:
    """
    프롬프트 목록 조회

    strategy_type이 'prompting-system' 또는 'prompting-user'인 전략들을 조회합니다.

    Args:
        session: 데이터베이스 세션
        prompt_type: 필터링할 프롬프트 유형 (system 또는 user)
    Returns:
        프롬프트 목록
    """
    valid_types = [
        "prompting-system",
        "prompting-user",
    ]

    query = (
        select(Strategy)
        .join(Strategy.strategy_type)
        .options(selectinload(Strategy.strategy_type))
        .where(StrategyType.name.in_(valid_types))
        .order_by(Strategy.name.asc())
    )

    if prompt_type:
        target_type = f"prompting-{prompt_type}"
        query = query.where(StrategyType.name == target_type)

    result = await session.execute(query)
    strategies = result.scalars().all()

    return strategies


async def get_prompt_by_no(
    session: AsyncSession,
    prompt_no_str: str
) -> Optional[Strategy]:
    """
    프롬프트 상세 정보 조회

    strategy_type이 'prompting-system' 또는 'prompting-user'인 전략만 조회합니다.

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

    # 프롬프트 조회 (system/user 프롬프트만 필터링)
    query = (
        select(Strategy)
        .join(Strategy.strategy_type)
        .options(selectinload(Strategy.strategy_type))
        .where(
            Strategy.strategy_no == prompt_no_bytes,
            StrategyType.name.in_([
                "prompting-system",
                "prompting-user"
            ])
        )
    )

    result = await session.execute(query)
    prompt = result.scalar_one_or_none()

    return prompt
