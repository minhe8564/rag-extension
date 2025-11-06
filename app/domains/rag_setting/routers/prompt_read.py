"""
프롬프트 조회 라우터 (목록 + 상세)
"""
from typing import Dict, Any
import math
import uuid

from fastapi import APIRouter, Depends, Query, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession

from ....core.database import get_db
from ....core.schemas import BaseResponse, Result
from ....core.check_role import check_role
from ....core.error_responses import admin_only_responses, not_found_error_response
from ..schemas.prompt import PromptListItem, PaginationInfo, PromptDetailResponse
from ..services.prompt_read import list_prompts, get_prompt_by_no


router = APIRouter(prefix="/rag", tags=["RAG - Prompt Management"])


def _bytes_to_uuid_str(b: bytes) -> str:
    """UUID 바이너리를 문자열로 변환"""
    try:
        return str(uuid.UUID(bytes=b))
    except Exception:
        return b.hex()


@router.get(
    "/prompts",
    response_model=BaseResponse[Dict[str, Any]],
    summary="프롬프트 목록 조회",
    description="프롬프트 목록을 조회합니다. 관리자만 접근 가능합니다.",
    responses=admin_only_responses()
)
async def get_prompts(
    pageNum: int = Query(1, ge=1, description="페이지 번호"),
    pageSize: int = Query(20, ge=1, le=100, description="페이지 크기"),
    sort: str = Query("name", description="정렬 기준"),
    x_user_role: str = Depends(check_role("ADMIN")),
    x_user_uuid: str = Header(..., alias="x-user-uuid"),
    session: AsyncSession = Depends(get_db)
):
    """
    프롬프트 목록 조회

    Args:
        pageNum: 페이지 번호 (1부터 시작)
        pageSize: 페이지 크기 (1-100)
        sort: 정렬 기준 (기본: name)
        x_user_role: 사용자 역할 (헤더)
        x_user_uuid: 사용자 UUID (헤더)
        session: 데이터베이스 세션

    Returns:
        BaseResponse: 프롬프트 목록과 페이지네이션 정보
    """
    # 프롬프트 목록 조회
    prompts, total_items = await list_prompts(
        session=session,
        page_num=pageNum,
        page_size=pageSize,
        sort_by=sort
    )

    # 응답 데이터 변환
    items = [
        PromptListItem(
            promptNo=_bytes_to_uuid_str(prompt.strategy_no),
            name=prompt.name,
            type=prompt.parameter.get("type", "system") if prompt.parameter else "system",
            content=prompt.description
        )
        for prompt in prompts
    ]

    # 페이지네이션 정보
    total_pages = math.ceil(total_items / pageSize) if total_items > 0 else 0
    has_next = pageNum < total_pages

    pagination = PaginationInfo(
        pageNum=pageNum,
        pageSize=pageSize,
        totalItems=total_items,
        totalPages=total_pages,
        hasNext=has_next
    )

    return BaseResponse[Dict[str, Any]](
        status=200,
        code="OK",
        message="성공",
        isSuccess=True,
        result=Result(data={"data": items, "pagination": pagination})
    )


@router.get(
    "/prompts/{promptNo}",
    response_model=BaseResponse[PromptDetailResponse],
    summary="프롬프트 상세 조회",
    description="특정 프롬프트의 상세 정보를 조회합니다. 관리자만 접근 가능합니다.",
    responses={
        **admin_only_responses(),
        404: not_found_error_response("프롬프트"),
    }
)
async def get_prompt_detail(
    promptNo: str,
    x_user_role: str = Depends(check_role("ADMIN")),
    x_user_uuid: str = Header(..., alias="x-user-uuid"),
    session: AsyncSession = Depends(get_db)
):
    """
    프롬프트 상세 정보 조회

    Args:
        promptNo: 프롬프트 ID (UUID)
        x_user_role: 사용자 역할 (헤더)
        x_user_uuid: 사용자 UUID (헤더)
        session: 데이터베이스 세션

    Returns:
        BaseResponse[PromptDetailResponse]: 프롬프트 상세 정보

    Raises:
        HTTPException 404: 프롬프트를 찾을 수 없음
    """
    # 프롬프트 조회
    prompt = await get_prompt_by_no(session, promptNo)

    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="대상을 찾을 수 없습니다."
        )

    # 응답 데이터 변환
    detail = PromptDetailResponse(
        promptNo=_bytes_to_uuid_str(prompt.strategy_no),
        name=prompt.name,
        type=prompt.parameter.get("type", "system") if prompt.parameter else "system",
        content=prompt.description
    )

    return BaseResponse[PromptDetailResponse](
        status=200,
        code="OK",
        message="성공",
        isSuccess=True,
        result=Result(data=detail)
    )
