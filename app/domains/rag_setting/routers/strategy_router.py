from __future__ import annotations

from typing import Optional, Dict, Any
import math
import uuid

from fastapi import APIRouter, Depends, Query, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ....common.db import get_session
from ....common.schemas import BaseResponse, Result
from ..schemas.strategy import StrategyListItem, PaginationInfo, StrategyDetailResponse
from ..services.strategy import list_strategies as list_strategies_service, get_strategy_by_no


router = APIRouter(prefix="/rag", tags=["RAG - Strategy Management"])


def _bytes_to_uuid_str(b: bytes) -> str:
    """UUID 바이너리를 문자열로 변환"""
    try:
        return str(uuid.UUID(bytes=b))
    except Exception:
        return b.hex()


class RoleChecker:
    """역할 기반 권한 체크"""

    def __init__(self, *allowed_roles: str, allow_anonymous: bool = False) -> None:
        self.allowed_roles = allowed_roles
        self.allow_anonymous = allow_anonymous

    async def __call__(
        self,
        x_user_role: str | None = Header(
            None,
            alias="x-user-role",
            description="사용자 역할 (예: USER, ADMIN)",
        ),
    ) -> str:
        if x_user_role is None:
            if self.allow_anonymous:
                return "ANONYMOUS"
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="x-user-role 헤더가 필요합니다.",
            )

        if self.allowed_roles and x_user_role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="요청을 수행할 권한이 없습니다.",
            )

        return x_user_role


@router.get(
    "/strategies",
    response_model=BaseResponse[Dict[str, Any]],
    summary="전략 목록 조회 (관리자 전용)",
    description="RAG 전략 목록을 조회합니다. 관리자만 접근 가능합니다.",
    responses={
        200: {"description": "성공"},
        400: {
            "description": "잘못된 요청 (유효성 검증 실패)",
            "content": {
                "application/json": {
                    "example": {
                        "status": 400,
                        "code": "VALIDATION_FAILED",
                        "message": "요청 파라미터 유효성 검증에 실패했습니다.",
                        "isSuccess": False,
                        "result": {
                            "errors": [
                                {
                                    "field": "pageNum",
                                    "message": "페이지 번호는 1 이상이어야 합니다."
                                }
                            ]
                        }
                    }
                }
            }
        },
        401: {
            "description": "인증 실패 (Access Token 없음 또는 유효하지 않음)",
            "content": {
                "application/json": {
                    "example": {
                        "status": 401,
                        "code": "INVALID_ACCESS_TOKEN",
                        "message": "엑세스 토큰이 유효하지 않거나 만료되었습니다.",
                        "isSuccess": False,
                        "result": {}
                    }
                }
            }
        },
        403: {
            "description": "권한 없음 (관리자 권한 필요)",
            "content": {
                "application/json": {
                    "example": {
                        "status": 403,
                        "code": "FORBIDDEN",
                        "message": "요청을 수행할 권한이 없습니다.",
                        "isSuccess": False,
                        "result": {
                            "requiredRole": ["ADMIN"]
                        }
                    }
                }
            }
        },
    },
)
async def get_strategies(
    type: Optional[str] = Query(None, description="전략 유형 필터"),
    pageNum: int = Query(1, ge=1, description="페이지 번호"),
    pageSize: int = Query(20, ge=1, le=100, description="페이지 크기"),
    sort: str = Query("name", description="정렬 기준"),
    session: AsyncSession = Depends(get_session),
    role: str = Depends(RoleChecker("ADMIN")),
):
    """
    전략 목록 조회

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
        200: {"description": "성공"},
        400: {
            "description": "잘못된 요청 (유효성 검증 실패)",
            "content": {
                "application/json": {
                    "example": {
                        "status": 400,
                        "code": "VALIDATION_FAILED",
                        "message": "유효하지 않은 전략 ID 형식입니다.",
                        "isSuccess": False,
                        "result": {
                            "errors": [
                                {
                                    "field": "strategyNo",
                                    "message": "UUID 형식이어야 합니다."
                                }
                            ]
                        }
                    }
                }
            }
        },
        401: {
            "description": "인증 실패 (Access Token 없음 또는 유효하지 않음)",
            "content": {
                "application/json": {
                    "example": {
                        "status": 401,
                        "code": "INVALID_ACCESS_TOKEN",
                        "message": "엑세스 토큰이 유효하지 않거나 만료되었습니다.",
                        "isSuccess": False,
                        "result": {}
                    }
                }
            }
        },
        403: {
            "description": "권한 없음 (관리자 권한 필요)",
            "content": {
                "application/json": {
                    "example": {
                        "status": 403,
                        "code": "FORBIDDEN",
                        "message": "요청을 수행할 권한이 없습니다.",
                        "isSuccess": False,
                        "result": {
                            "requiredRole": ["ADMIN"]
                        }
                    }
                }
            }
        },
        404: {
            "description": "전략을 찾을 수 없음",
            "content": {
                "application/json": {
                    "example": {
                        "status": 404,
                        "code": "NOT_FOUND",
                        "message": "전략을 찾을 수 없습니다.",
                        "isSuccess": False,
                        "result": {}
                    }
                }
            }
        },
    },
)
async def get_strategy_detail(
    strategyNo: str,
    session: AsyncSession = Depends(get_session),
    role: str = Depends(RoleChecker("ADMIN")),
):
    """
    전략 상세 정보 조회

    Args:
        strategyNo: 전략 ID (UUID)

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
