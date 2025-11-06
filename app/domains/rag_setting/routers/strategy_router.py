from typing import Optional, Dict, Any
import math
import uuid

from fastapi import APIRouter, Depends, Query, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession

from ....core.database import get_db
from ....core.schemas import BaseResponse, Result
from ....core.error_responses import (
    not_found_error_response,
    conflict_error_response,
    public_endpoint_responses,
    unauthorized_error_response,
)
from ..schemas.strategy import (
    StrategyListItem,
    PaginationInfo,
    StrategyDetailResponse,
    StrategyCreateRequest,
    StrategyCreateResponse,
    StrategyUpdateRequest,
    StrategyUpdateResponse,
    StrategyTypeListItem,
    StrategyTypeListResponse,
    StrategyTypeCreateRequest,
    StrategyTypeCreateResponse,
    StrategyTypeUpdateRequest,
    StrategyTypeUpdateResponse,
)
from ..services.strategy import (
    list_strategies as list_strategies_service,
    get_strategy_by_no,
    create_strategy as create_strategy_service,
    update_strategy as update_strategy_service,
    delete_strategy as delete_strategy_service,
    list_strategy_types as list_strategy_types_service,
    create_strategy_type as create_strategy_type_service,
    update_strategy_type as update_strategy_type_service,
    delete_strategy_type as delete_strategy_type_service,
    delete_strategy_type_by_name as delete_strategy_type_by_name_service,
)


router = APIRouter(
    prefix="/rag",
    tags=["RAG - Strategy Management"],
)


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
        401: unauthorized_error_response(),
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


@router.put(
    "/strategies/{strategyNo}",
    response_model=BaseResponse[StrategyUpdateResponse],
    summary="전략 수정",
    description="전략 정보를 수정합니다.",
    responses={
        200: {"description": "전략 수정 성공"},
        400: {"description": "잘못된 전략 ID"},
        401: unauthorized_error_response(),
        404: not_found_error_response("전략"),
        409: conflict_error_response("전략"),
    },
)
async def update_strategy(
    strategyNo: str,
    request: StrategyUpdateRequest,
    session: AsyncSession = Depends(get_db),
):
    """전략 수정"""

    strategy = await update_strategy_service(
        session=session,
        strategy_no_str=strategyNo,
        name=request.name,
        description=request.description,
        parameter=request.parameter,
        strategy_type_name=request.strategy_type,
    )

    return BaseResponse[StrategyUpdateResponse](
        status=200,
        code="OK",
        message="전략 수정에 성공하였습니다.",
        isSuccess=True,
        result=Result(
            data=StrategyUpdateResponse(
                strategyNo=_bytes_to_uuid_str(strategy.strategy_no),
                name=strategy.name,
                description=strategy.description,
                type=strategy.strategy_type.name if strategy.strategy_type else "",
                parameter=strategy.parameter,
            )
        ),
    )


@router.delete(
    "/strategies/{strategyNo}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="전략 삭제",
    description="특정 전략을 삭제합니다.",
    responses={
        204: {"description": "전략 삭제 성공"},
        400: {
            "description": "잘못된 전략 ID",
        },
        401: unauthorized_error_response(),
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
    "/strategies/types",
    response_model=BaseResponse[StrategyTypeListResponse],
    summary="전략 유형 목록 조회",
    description="전략 유형 목록을 조회합니다.",
    responses={
        200: {"description": "전략 유형 목록 조회 성공"},
        401: unauthorized_error_response(),
    },
)
async def get_strategy_types(
    session: AsyncSession = Depends(get_db),
):
    """전략 유형 목록 조회"""

    strategy_types = await list_strategy_types_service(session=session)

    items = [
        StrategyTypeListItem(
            strategyTypeNo=_bytes_to_uuid_str(strategy_type.strategy_type_no),
            name=strategy_type.name,
        )
        for strategy_type in strategy_types
    ]

    return BaseResponse[StrategyTypeListResponse](
        status=200,
        code="OK",
        message="전략 유형 목록 조회에 성공하였습니다.",
        isSuccess=True,
        result=Result(data=StrategyTypeListResponse(data=items)),
    )


@router.post(
    "/strategies/types",
    response_model=BaseResponse[StrategyTypeCreateResponse],
    status_code=status.HTTP_201_CREATED,
    summary="전략 유형 생성",
    description="새로운 전략 유형을 생성합니다.",
    responses={
        201: {"description": "전략 유형 생성 성공"},
        401: unauthorized_error_response(),
        409: conflict_error_response("전략 유형"),
    },
)
async def create_strategy_type(
    request: StrategyTypeCreateRequest,
    session: AsyncSession = Depends(get_db),
):
    """전략 유형 생성"""

    strategy_type = await create_strategy_type_service(session=session, name=request.name)

    return BaseResponse[StrategyTypeCreateResponse](
        status=201,
        code="CREATED",
        message="전략 유형 생성에 성공하였습니다.",
        isSuccess=True,
        result=Result(
            data=StrategyTypeCreateResponse(
                strategyTypeNo=_bytes_to_uuid_str(strategy_type.strategy_type_no)
            )
        ),
    )


@router.put(
    "/strategies/types/{typeNo}",
    response_model=BaseResponse[StrategyTypeUpdateResponse],
    summary="전략 유형 이름 수정",
    description="전략 유형 이름을 수정합니다.",
    responses={
        200: {"description": "전략 유형 수정 성공"},
        400: {"description": "잘못된 전략 유형 ID"},
        401: unauthorized_error_response(),
        404: not_found_error_response("전략 유형"),
        409: conflict_error_response("전략 유형"),
    },
)
async def update_strategy_type(
    typeNo: str,
    request: StrategyTypeUpdateRequest,
    session: AsyncSession = Depends(get_db),
):
    """전략 유형 이름 수정"""

    strategy_type = await update_strategy_type_service(
        session=session,
        strategy_type_no_str=typeNo,
        name=request.name,
    )

    return BaseResponse[StrategyTypeUpdateResponse](
        status=200,
        code="OK",
        message="전략 유형 수정에 성공하였습니다.",
        isSuccess=True,
        result=Result(
            data=StrategyTypeUpdateResponse(
                strategyTypeNo=_bytes_to_uuid_str(strategy_type.strategy_type_no),
                name=strategy_type.name,
            )
        ),
    )


@router.delete(
    "/strategies/types/{typeNo}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="전략 유형 삭제",
    description="특정 전략 유형을 삭제합니다.",
    responses={
        204: {"description": "전략 유형 삭제 성공"},
        400: {"description": "잘못된 전략 유형 ID"},
        401: unauthorized_error_response(),
        404: not_found_error_response("전략 유형"),
        409: conflict_error_response("전략 유형"),
    },
)
async def delete_strategy_type(
    typeNo: str,
    session: AsyncSession = Depends(get_db),
):
    """전략 유형 삭제"""

    await delete_strategy_type_service(session=session, strategy_type_no_str=typeNo)

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete(
    "/strategies/types",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="전략 유형 삭제 (이름)",
    description="전략 유형 이름으로 전략 유형을 삭제합니다.",
    responses={
        204: {"description": "전략 유형 삭제 성공"},
        401: unauthorized_error_response(),
        404: not_found_error_response("전략 유형"),
        409: conflict_error_response("전략 유형"),
    },
)
async def delete_strategy_type_by_name(
    name: str = Query(..., description="삭제할 전략 유형 이름"),
    session: AsyncSession = Depends(get_db),
):
    """전략 유형을 이름으로 삭제"""

    await delete_strategy_type_by_name_service(session=session, name=name)

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/strategies",
    response_model=BaseResponse[Dict[str, Any]],
    summary="전략 목록 조회",
    description="RAG 전략 목록을 조회합니다.",
    responses={**public_endpoint_responses(), 401: unauthorized_error_response()},
)
async def get_strategies(
    type: Optional[str] = Query(None, description="전략 유형 필터"),
    pageNum: int = Query(1, ge=1, description="페이지 번호"),
    pageSize: int = Query(20, ge=1, le=100, description="페이지 크기"),
    sort: str = Query("name", description="정렬 기준"),
    session: AsyncSession = Depends(get_db),
):
    """
    전략 목록 조회

    Args:
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
    summary="전략 상세 조회",
    description="특정 전략의 상세 정보를 조회합니다.",
    responses={
        401: unauthorized_error_response(),
        404: not_found_error_response("전략"),
    },
)
async def get_strategy_detail(
    strategyNo: str,
    session: AsyncSession = Depends(get_db),
):
    """
    전략 상세 정보 조회

    Args:
        strategyNo: 전략 ID (UUID)
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
