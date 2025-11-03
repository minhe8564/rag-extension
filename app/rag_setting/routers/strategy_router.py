"""
RAG Strategy Router
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Header, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import Optional
from app.db import get_session
from app.rag_setting.models.strategy import Strategy, StrategyType
from app.rag_setting.schemas.strategy import (
    StrategyResponse,
    PaginationResponse,
    StrategyListResult,
    StandardResponse,
    ErrorResponse
)
import math

router = APIRouter(
    prefix="/rag",
    tags=["RAG - Strategy Management"]
)


# 역할 기반 권한 체크 클래스
class RoleChecker:
    """FastAPI dependency that validates the custom `x-user-role` header."""

    def __init__(self, *allowed_roles: str, allow_anonymous: bool = False) -> None:
        self.allowed_roles = allowed_roles
        self.allow_anonymous = allow_anonymous

    async def __call__(
        self,
        x_user_role: str | None = Header(
            default=None,
            alias="x-user-role",
            description="게이트웨이가 전달하는 사용자 역할 헤더 (예: USER, ADMIN)",
        ),
    ) -> str:
        if x_user_role is None:
            if self.allow_anonymous:
                return "ANONYMOUS"
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "status": 401,
                    "code": "INVALID_ACCESS_TOKEN",
                    "message": "x-user-role 헤더가 필요합니다.",
                    "isSuccess": False,
                    "result": {}
                }
            )

        if self.allowed_roles and x_user_role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "status": 403,
                    "code": "FORBIDDEN",
                    "message": "요청을 수행할 권한이 없습니다.",
                    "isSuccess": False,
                    "result": {
                        "requiredRole": list(self.allowed_roles)
                    }
                }
            )

        return x_user_role


@router.get(
    "/strategies",
    response_model=StandardResponse,
    summary="전략 목록 조회",
    description="RAG 전략 목록을 조회합니다. 타입별 필터링, 페이지네이션, 정렬을 지원합니다.",
    responses={
        200: {"description": "성공"},
        401: {"model": ErrorResponse, "description": "인증 토큰 오류"},
        403: {"model": ErrorResponse, "description": "권한 없음"}
    }
)
async def get_strategies(
    type: Optional[str] = Query(
        None,
        description="검색할 전략 유형 (extraction, chunking, embedding, etc.)"
    ),
    pageNum: int = Query(1, ge=1, description="조회할 페이지 번호 (기본: 1)"),
    pageSize: int = Query(20, ge=1, le=100, description="페이지 당 항목 수 (기본: 20, 최대: 100)"),
    sort: str = Query("name", description="정렬 기준 (기본: name)"),
    db: AsyncSession = Depends(get_session),
    role: str = Depends(RoleChecker("USER", "ADMIN"))
):
    """
    전략 목록 조회 API

    - **type**: 전략 유형으로 필터링 (선택)
    - **pageNum**: 페이지 번호 (1부터 시작)
    - **pageSize**: 페이지당 항목 수 (1-100)
    - **sort**: 정렬 기준 (현재 name만 지원)

    Returns:
        StandardResponse: 전략 목록과 페이지네이션 정보
    """

    # 1. 기본 쿼리 생성 (StrategyType도 함께 로드)
    query = select(Strategy).options(
        selectinload(Strategy.strategy_type)  # N+1 쿼리 방지
    )

    # 2. 타입 필터링 (StrategyType.name으로 필터)
    if type:
        query = query.join(Strategy.strategy_type).where(StrategyType.name == type)

    # 3. 정렬
    if sort == "name":
        query = query.order_by(Strategy.name.asc())
    else:
        query = query.order_by(Strategy.name.asc())  # 기본값

    # 4. 전체 항목 수 조회 (페이지네이션 계산용)
    count_query = select(func.count()).select_from(Strategy)
    if type:
        count_query = count_query.join(Strategy.strategy_type).where(StrategyType.name == type)

    result_count = await db.execute(count_query)
    total_items = result_count.scalar()

    # 5. 페이지네이션 적용
    offset = (pageNum - 1) * pageSize
    query = query.offset(offset).limit(pageSize)

    # 6. 데이터 조회
    result = await db.execute(query)
    strategies = result.scalars().all()

    # 7. 페이지네이션 정보 계산
    total_pages = math.ceil(total_items / pageSize) if total_items > 0 else 0
    has_next = pageNum < total_pages

    # 8. 응답 데이터 변환
    strategy_list = [
        StrategyResponse.from_strategy(strategy)
        for strategy in strategies
    ]

    # 9. 표준 응답 형식 반환
    return StandardResponse(
        status=200,
        code="OK",
        message="성공",
        isSuccess=True,
        result=StrategyListResult(
            data=strategy_list,
            pagination=PaginationResponse(
                pageNum=pageNum,
                pageSize=pageSize,
                totalItems=total_items,
                totalPages=total_pages,
                hasNext=has_next
            )
        )
    )
