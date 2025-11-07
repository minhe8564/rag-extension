"""
프롬프트 삭제 서비스
"""
from __future__ import annotations

import uuid

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from ..models.strategy import Strategy, StrategyType


async def delete_prompt(
    session: AsyncSession,
    prompt_no_str: str
) -> bool:
    """
    프롬프트 삭제

    strategy_type='prompting-system' 또는 'prompting-user'인 전략만 삭제합니다.

    Args:
        session: 데이터베이스 세션
        prompt_no_str: 프롬프트 ID (UUID 문자열)

    Returns:
        삭제 성공 여부

    Raises:
        HTTPException: 404 - 프롬프트를 찾을 수 없음
    """
    try:
        # UUID 문자열을 바이너리로 변환
        prompt_no_bytes = uuid.UUID(prompt_no_str).bytes
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="대상을 찾을 수 없습니다."
        )

    # 1. 프롬프트 존재 확인
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

    # 2. 프롬프트 삭제
    delete_query = delete(Strategy).where(
        Strategy.strategy_no == prompt_no_bytes
    )

    await session.execute(delete_query)
    await session.commit()

    return True
