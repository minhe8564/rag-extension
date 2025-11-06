from typing import Optional, Dict, Any
import math
import uuid

from fastapi import APIRouter, Depends, Query, HTTPException, status, Header, Response
from sqlalchemy.ext.asyncio import AsyncSession

from ....core.database import get_db
from ....core.schemas import BaseResponse, Result
from ....core.check_role import check_role
from ....core.error_responses import admin_only_responses, not_found_error_response, conflict_error_response
from ..schemas.strategy import (
    StrategyListItem,
    PaginationInfo,
    StrategyDetailResponse,
    StrategyCreateRequest,
    StrategyCreateResponse,
)
from ..services.strategy import (
    list_strategies as list_strategies_service,
    get_strategy_by_no,
    create_strategy as create_strategy_service,
    delete_strategy as delete_strategy_service,
)


router = APIRouter(prefix="/rag", tags=["RAG - Strategy Management"])


def _bytes_to_uuid_str(b: bytes) -> str:
    """UUID 바이너리를 문자열로 변환"""
    try:
        return str(uuid.UUID(bytes=b))
    except Exception:
        return b.hex()


@router.post(
    "/strategies",
    response_model=BaseResponse[StrategyCreateResponse],
    status_code=status.HTTP_201_CREATED,
    summary="전략 생성",
    description="새로운 RAG 전략을 생성합니다.",
    responses={
        201: {"description": "전략 생성 성공"},
        404: not_found_error_response("전략 유형"),
        409: conflict_error_response("전략"),
    },
)
async def create_strategy(
    request: StrategyCreateRequest,
    session: AsyncSession = Depends(get_db),
):
    """
    전략 생성

    Args:
        request: 전략 생성 요청 본문

    Returns:
        BaseResponse[StrategyCreateResponse]: 생성된 전략 ID
    """

    strategy = await create_strategy_service(
        session=session,
        name=request.name,
        description=request.description,
        parameter=request.parameter,
        strategy_type_name=request.strategy_type,
    )

    return BaseResponse[StrategyCreateResponse](
        status=201,
        code="CREATED",
        message="전략 생성에 성공하였습니다.",
        isSuccess=True,
        result=Result(
            data=StrategyCreateResponse(
                strategyNo=_bytes_to_uuid_str(strategy.strategy_no)
            )
        ),
    )


@router.delete(
    "/strategy/{strategyNo}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="전략 삭제",
    description="특정 전략을 삭제합니다.",
    responses={
        204: {"description": "전략 삭제 성공"},
        400: {
            "description": "잘못된 전략 ID",
        },
        404: not_found_error_response("전략"),
        409: conflict_error_response("전략"),
    },
)
async def delete_strategy(
    strategyNo: str,
    session: AsyncSession = Depends(get_db),
):
    """전략 삭제"""

    await delete_strategy_service(session=session, strategy_no_str=strategyNo)

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/strategies",
    response_model=BaseResponse[Dict[str, Any]],
    summary="전략 목록 조회 (관리자 전용)",
    description="RAG 전략 목록을 조회합니다. 관리자만 접근 가능합니다.",
    responses=admin_only_responses(),
)
async def get_strategies(
    type: Optional[str] = Query(None, description="전략 유형 필터"),
    pageNum: int = Query(1, ge=1, description="페이지 번호"),
    pageSize: int = Query(20, ge=1, le=100, description="페이지 크기"),
    sort: str = Query("name", description="정렬 기준"),
    x_user_role: str = Depends(check_role("ADMIN")),
    session: AsyncSession = Depends(get_db),
):
    """
    전략 목록 조회

    Args:
        x_user_role: 사용자 역할 (헤더, 전역 security에서 자동 주입)
        session: 데이터베이스 세션

    Returns:
        BaseResponse: 전략 목록과 페이지네이션 정보
    """
    strategies, total_items = await list_strategies_service(
        session=session,
        type_filter=type,
        page_num=pageNum,
        page_size=pageSize,
        sort_by=sort,
    )

    # 응답 데이터 변환
    items = [
        StrategyListItem(
            strategyNo=_bytes_to_uuid_str(strategy.strategy_no),
            name=strategy.name,
            description=strategy.description,
            type=strategy.strategy_type.name if strategy.strategy_type else "",
            parameter=strategy.parameter,
        )
        for strategy in strategies
    ]

    # 페이지네이션 정보
    total_pages = math.ceil(total_items / pageSize) if total_items > 0 else 0
    has_next = pageNum < total_pages

    pagination = PaginationInfo(
        pageNum=pageNum,
        pageSize=pageSize,
        totalItems=total_items,
        totalPages=total_pages,
        hasNext=has_next,
    )

    return BaseResponse[Dict[str, Any]](
        status=200,
        code="OK",
        message="전략 목록 조회에 성공하였습니다.",
        isSuccess=True,
        result=Result(data={"data": items, "pagination": pagination}),
    )


@router.get(
    "/strategies/{strategyNo}",
    response_model=BaseResponse[StrategyDetailResponse],
    summary="전략 상세 조회 (관리자 전용)",
    description="특정 전략의 상세 정보를 조회합니다. 관리자만 접근 가능합니다.",
    responses={
        **admin_only_responses(),
        404: not_found_error_response("전략"),
    },
)
async def get_strategy_detail(
    strategyNo: str,
    x_user_role: str = Depends(check_role("ADMIN")),
    session: AsyncSession = Depends(get_db),
):
    """
    전략 상세 정보 조회

    Args:
        strategyNo: 전략 ID (UUID)
        x_user_role: 사용자 역할 (헤더, 전역 security에서 자동 주입)
        session: 데이터베이스 세션

    Returns:
        BaseResponse[StrategyDetailResponse]: 전략 상세 정보
    """
    # 전략 조회
    strategy = await get_strategy_by_no(session, strategyNo)

    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="전략을 찾을 수 없습니다.",
        )

    # 응답 데이터 변환
    detail = StrategyDetailResponse(
        strategyNo=_bytes_to_uuid_str(strategy.strategy_no),
        name=strategy.name,
        description=strategy.description,
        type=strategy.strategy_type.name if strategy.strategy_type else "",
        parameters=strategy.parameter,
    )

    return BaseResponse[StrategyDetailResponse](
        status=200,
        code="OK",
        message="성공",
        isSuccess=True,
        result=Result(data=detail),
    )
