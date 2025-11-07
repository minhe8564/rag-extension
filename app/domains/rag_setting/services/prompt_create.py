"""
프롬프트 생성 서비스
"""
from __future__ import annotations

from typing import Optional
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from ..models.strategy import Strategy, StrategyType, generate_uuid_binary


async def get_prompting_strategy_type(
    session: AsyncSession,
    prompt_type: str
) -> StrategyType:
    """
    prompting 전략 유형 조회 (prompting-system 또는 prompting-user)

    전략 유형이 세분화되어 system과 user로 분리되었습니다.

    Args:
        session: 데이터베이스 세션
        prompt_type: 프롬프트 유형 ('system' 또는 'user')

    Returns:
        StrategyType 객체

    Raises:
        HTTPException: 500 - 전략 유형을 찾을 수 없음
    """
    # prompt_type에 따라 전략 유형 이름 결정
    strategy_type_name = f"prompting-{prompt_type}"

    query = select(StrategyType).where(StrategyType.name == strategy_type_name)
    result = await session.execute(query)
    strategy_type = result.scalar_one_or_none()

    if not strategy_type:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"전략 유형 '{strategy_type_name}'을 찾을 수 없습니다. 데이터베이스 초기화를 확인해주세요."
        )

    return strategy_type


async def check_prompt_name_exists(
    session: AsyncSession,
    name: str,
    prompt_type: str
) -> bool:
    """
    프롬프트 이름 중복 확인

    prompting-system 또는 prompting-user 전략 유형 내에서 같은 이름이 있는지 확인합니다.

    Args:
        session: 데이터베이스 세션
        name: 프롬프트 이름
        prompt_type: 프롬프트 유형 ('system' 또는 'user')

    Returns:
        중복 여부 (True: 중복 존재, False: 중복 없음)
    """
    # 전략 유형 이름 생성
    strategy_type_name = f"prompting-{prompt_type}"

    # prompting-system 또는 prompting-user 전략 유형의 전략 중에서 같은 이름이 있는지 확인
    query = (
        select(Strategy)
        .join(Strategy.strategy_type)
        .where(
            Strategy.name == name,
            StrategyType.name == strategy_type_name
        )
    )

    result = await session.execute(query)
    existing_strategy = result.scalar_one_or_none()

    return existing_strategy is not None


async def create_prompt(
    session: AsyncSession,
    name: str,
    prompt_type: str,
    description: str,
    content: str
) -> str:
    """
    프롬프트 생성

    프롬프트는 Strategy 테이블에 strategy_type='prompting'으로 저장됩니다.
    - description: 요약 설명 (Strategy.description, 최대 255자)
    - content: 실제 프롬프트 내용 (parameter JSON, 제한 없음)
    - type: 프롬프트 유형 (parameter JSON 메타데이터)

    실제 system/user 구분은 QUERY_GROUP 테이블에서 어느 필드에 참조되는지로 결정됩니다.

    Args:
        session: 데이터베이스 세션
        name: 프롬프트명
        prompt_type: 프롬프트 유형 (system 또는 user) - 메타데이터용
        description: 프롬프트 요약 설명 (최대 255자)
        content: 프롬프트 실제 내용 (제한 없음)

    Returns:
        생성된 프롬프트 ID (UUID 문자열)

    Raises:
        HTTPException: 409 - 중복된 이름 존재
        HTTPException: 500 - 전략 유형 생성 실패
    """
    # 1. 중복 이름 확인 (같은 타입 내에서만)
    if await check_prompt_name_exists(session, name, prompt_type):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="동일한 이름의 프롬프트가 존재합니다."
        )

    # 2. prompting-system 또는 prompting-user 전략 유형 조회
    strategy_type = await get_prompting_strategy_type(session, prompt_type)

    # 3. 프롬프트(전략) 생성
    new_strategy = Strategy(
        strategy_no=generate_uuid_binary(),
        strategy_type_no=strategy_type.strategy_type_no,
        name=name,
        description=description,  # 요약 설명 (최대 255자)
        parameter={
            "content": content,  # 실제 프롬프트 내용 (제한 없음)
            "type": prompt_type  # 메타데이터
        }
    )

    session.add(new_strategy)
    await session.commit()
    await session.refresh(new_strategy)

    # 4. UUID 문자열로 변환하여 반환
    prompt_no = str(uuid.UUID(bytes=new_strategy.strategy_no))

    return prompt_no
