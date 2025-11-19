from typing import Optional, Dict, Any
import uuid

from fastapi import APIRouter, Depends, Query, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession

from ....core.database import get_db
from ....core.schemas import BaseResponse
from ....core.auth.check_role import check_role
from ....core.config import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from ..schemas.strategy import (
    StrategyListItem,
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
)


router = APIRouter(
    prefix="/rag",
    tags=["RAG - Strategy Management"],
    dependencies=[Depends(check_role("ADMIN"))],
)


def _bytes_to_uuid_str(b: bytes) -> str:
    """UUID 바이너리를 문자열로 변환"""
    try:
        return str(uuid.UUID(bytes=b))
    except Exception:
        return b.hex()


@router.get(
    "/strategies/types",
    response_model=BaseResponse[StrategyTypeListResponse],
    summary="[관리자] 전략 유형 목록 조회",
    description="전략 유형 목록을 조회합니다.",
    responses={
        200: {
            "description": "전략 유형 목록 조회에 성공하였습니다.",
            "content": {
                "application/json": {
                    "example": {
                        "status": 200,
                        "code": "OK",
                        "message": "전략 유형 목록 조회에 성공하였습니다.",
                        "isSuccess": True,
                        "result": {
                            "data": [
                                {
                                    "strategyTypeNo": "7ab054c9-8b1a-4ff3-8ff7-c64a48fc6141",
                                    "name": "chunking"
                                },
                                {
                                    "strategyTypeNo": "e7a2e663-bd65-4fc6-ad85-c9413a7f4380",
                                    "name": "embedding-dense"
                                }
                            ]
                        }
                    }
                }
            }
        }
    }
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
        result=StrategyTypeListResponse(data=items),
    )


@router.post(
    "/strategies/types",
    response_model=BaseResponse[StrategyTypeCreateResponse],
    status_code=status.HTTP_201_CREATED,
    summary="[관리자] 전략 유형 생성",
    description="새로운 전략 유형을 생성합니다.",
    responses={
        201: {
            "description": "전략 유형 생성에 성공하였습니다.",
            "content": {
                "application/json": {
                    "example": {
                        "status": 201,
                        "code": "CREATED",
                        "message": "전략 유형 생성에 성공하였습니다.",
                        "isSuccess": True,
                        "result": {
                            "strategyTypeNo": "7ab054c9-8b1a-4ff3-8ff7-c64a48fc6141"
                        }
                    }
                }
            }
        }
    }
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
        result=StrategyTypeCreateResponse(strategyTypeNo=_bytes_to_uuid_str(strategy_type.strategy_type_no)
        ),
    )


@router.put(
    "/strategies/types/{typeNo}",
    response_model=BaseResponse[StrategyTypeUpdateResponse],
    summary="[관리자] 전략 유형 이름 수정",
    description="전략 유형 이름을 수정합니다.",
    responses={
        200: {
            "description": "전략 유형 이름 수정에 성공하였습니다.",
            "content": {
                "application/json": {
                    "example": {
                        "status": 200,
                        "code": "OK",
                        "message": "전략 유형 이름 수정에 성공하였습니다.",
                        "isSuccess": True,
                        "result": { }
                    }
                }
            }
        }
    }
)
async def update_strategy_type(
    typeNo: str,
    request: StrategyTypeUpdateRequest,
    session: AsyncSession = Depends(get_db),
):
    """전략 유형 이름 수정"""

    await update_strategy_type_service(
        session=session,
        strategy_type_no_str=typeNo,
        name=request.name,
    )

    return BaseResponse[StrategyTypeUpdateResponse](
        status=200,
        code="OK",
        message="전략 유형 수정에 성공하였습니다.",
        isSuccess=True,
        result={},
    )


@router.delete(
    "/strategies/types/{typeNo}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="전략 유형 삭제 (관리자)",
    description="특정 전략 유형을 삭제합니다.",
)
async def delete_strategy_type(
    typeNo: str,
    session: AsyncSession = Depends(get_db),
):
    """전략 유형 삭제"""

    await delete_strategy_type_service(session=session, strategy_type_no_str=typeNo)

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/strategies",
    response_model=BaseResponse[StrategyCreateResponse],
    status_code=status.HTTP_201_CREATED,
    summary="[관리자] 전략 생성",
    description="새로운 RAG 전략을 생성합니다.",
    responses={
        200: {
            "description": "전략 생성에 성공하였습니다.",
            "content": {
                "application/json": {
                    "example": {
                        "status": 200,
                        "code": "OK",
                        "message": "전략 생성에 성공하였습니다.",
                        "isSuccess": True,
                        "result": {
                            "strategyNo": "c4be4990-da6d-4f0b-92c8-04f430b0fd7f"
                        }
                    }   
                }
            }
        }
    }
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
        code=request.code,
        description=request.description,
        parameter=request.parameter,
        strategy_type_name=request.strategyType,
    )

    return BaseResponse[StrategyCreateResponse](
        status=201,
        code="CREATED",
        message="전략 생성에 성공하였습니다.",
        isSuccess=True,
        result=StrategyCreateResponse(strategyNo=_bytes_to_uuid_str(strategy.strategy_no)),
    )


@router.put(
    "/strategies/{strategyNo}",
    response_model=BaseResponse[StrategyUpdateResponse],
    summary="[관리자] 전략 수정",
    description="전략 정보를 수정합니다.",
    responses={
        200: {
            "description": "전략 수정에 성공하였습니다.",
            "content": {
                "application/json": {
                    "example": {
                        "status": 200,
                        "code": "OK",
                        "message": "전략 수정에 성공하였습니다.",
                        "isSuccess": True,
                        "result": { }
                    }
                }
            }
        }
    }
)
async def update_strategy(
    strategyNo: str,
    request: StrategyUpdateRequest,
    session: AsyncSession = Depends(get_db),
):
    """전략 수정"""

    updated_strategy = await update_strategy_service(
        session=session,
        strategy_no_str=strategyNo,
        name=request.name,
        code=request.code,
        description=request.description,
        parameter=request.parameter,
        strategy_type_name=request.strategyType,
    )

    return BaseResponse[StrategyUpdateResponse](
        status=200,
        code="OK",
        message="전략 수정에 성공하였습니다.",
        isSuccess=True,
        result={}
    )


@router.delete(
    "/strategies/{strategyNo}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="[관리자] 전략 삭제",
    description="특정 전략을 삭제합니다.",
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
    summary="[관리자] 전략 목록 조회",
    description="RAG 전략 목록을 조회합니다.",
    responses={
        200: {
            "description": "전략 목록 조회에 성공하였습니다.",
            "content": {
                "application/json": {
                    "example": {
                        "status": 200,
                        "code": "OK",
                        "message": "전략 목록 조회에 성공하였습니다.",
                        "isSuccess": True,
                        "result": {
                            "data": [
                                {
                                    "strategyNo": "c4be4990-da6d-4f0b-92c8-04f430b0fd7f",
                                    "code": "CHK_MD",
                                    "name": "MD 기반 청킹",
                                    "description": "MD 포맷을 분석해 청킹",
                                    "type": "chunking",
                                    "parameter": {
                                        "type": "md",
                                        "token": 512,
                                        "overlap": 40
                                    }
                                },
                                {
                                    "strategyNo": "2014c312-1284-4e06-bec5-327c42f6bc3b",
                                    "code": "CHK_FIXED",
                                    "name": "고정 길이 청킹",
                                    "description": "고정된 길이로 청크 분할",
                                    "type": "chunking",
                                    "parameter": {
                                        "type": "fixed",
                                        "token": 512,
                                        "overlap": 40
                                    }
                                },
                                {
                                    "strategyNo": "4ff1a9ba-0609-4adc-b0d8-f44d8741e242",
                                    "code": "CHK_SEMANTIC",
                                    "name": "의미 기반 청킹",
                                    "description": "유사한 문장을 묶어 청킹",
                                    "type": "chunking",
                                    "parameter": {
                                        "type": "semantic",
                                        "token": 512,
                                        "overlap": 40
                                    }
                                }
                            ],
                        }
                    }   
                }
            }
        }
    }
)
async def get_strategies(
    type: Optional[str] = Query(None, description="전략 유형 필터"),
    session: AsyncSession = Depends(get_db),
):
    """
    전략 목록 조회
    """
    strategies = await list_strategies_service(
        session=session,
        type_filter=type,
    )

    # 응답 데이터 변환
    items = [
        StrategyListItem(
            strategyNo=_bytes_to_uuid_str(strategy.strategy_no),
            code=strategy.code,
            name=strategy.name,
            description=strategy.description,
            type=strategy.strategy_type.name if strategy.strategy_type else "",
            parameter=strategy.parameter,
        )
        for strategy in strategies
    ]

    return BaseResponse[Dict[str, Any]](
        status=200,
        code="OK",
        message="전략 목록 조회에 성공하였습니다.",
        isSuccess=True,
        result={"data": items},
    )


@router.get(
    "/strategies/{strategyNo}",
    response_model=BaseResponse[StrategyDetailResponse],
    summary="[관리자] 전략 상세 조회",
    description="특정 전략의 상세 정보를 조회합니다.",
    responses={
        200: {
            "description": "전략 상세 조회에 성공하였습니다.",
            "content": {
                "application/json": {
                    "example": {
                        "status": 200,
                        "code": "OK",
                        "message": "전략 상세 조회에 성공하였습니다.",
                        "isSuccess": True,
                        "result": {
                            "strategyNo": "c4be4990-da6d-4f0b-92c8-04f430b0fd7f",
                            "code": "CHK_MD",
                            "name": "MD 기반 청킹",
                            "description": "MD 포맷을 분석해 청킹",
                            "type": "chunking",
                            "parameters": {
                            "type": "md",
                            "token": 512,
                            "overlap": 40
                            }
                        }
                    }
                }
            }
        }
    }
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
        code=strategy.code,
        name=strategy.name,
        description=strategy.description,
        type=strategy.strategy_type.name if strategy.strategy_type else "",
        parameters=strategy.parameter,
    )

    return BaseResponse[StrategyDetailResponse](
        status=200,
        code="OK",
        message="전략 상세 조회에 성공하였습니다.",
        isSuccess=True,
        result=detail,
    )
