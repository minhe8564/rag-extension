"""
Ingest 템플릿 조회 라우터 (목록 + 상세)
"""
import math
import uuid

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ....core.database import get_db
from ....core.schemas import BaseResponse, Result
from ....core.check_role import check_role
from ..schemas.ingest import (
    IngestGroupListItem,
    IngestGroupListResponse,
    IngestTemplateDetailResponse,
    StrategyItem,
)
from ..schemas.strategy import PaginationInfo
from ..services.ingest import list_ingest_groups, get_ingest_template_detail


router = APIRouter(prefix="/rag", tags=["RAG - Ingest Template Management"])
def _bytes_to_uuid_str(b: bytes) -> str:
    """UUID 바이너리를 문자열로 변환"""
    try:
        return str(uuid.UUID(bytes=b))
    except Exception:
        return b.hex()


@router.get(
    "/ingest-templates",
    response_model=BaseResponse[IngestGroupListResponse],
    summary="Ingest 템플릿 목록 조회 (관리자 전용)",
    description="Ingest 템플릿 목록을 조회합니다. 관리자만 접근 가능합니다.",
)
async def get_ingest_templates(
    pageNum: int = Query(1, ge=1, description="페이지 번호"),
    pageSize: int = Query(20, ge=1, le=100, description="페이지 크기"),
    sort: str = Query("created_at", description="정렬 기준"),
    x_user_role: str = Depends(check_role("ADMIN")),
    session: AsyncSession = Depends(get_db),
):
    """
    Ingest 템플릿 목록 조회

    Args:
        pageNum: 페이지 번호
        pageSize: 페이지 크기
        sort: 정렬 기준
        x_user_role: 사용자 역할 (헤더, 전역 security에서 자동 주입)
        session: 데이터베이스 세션

    Returns:
        BaseResponse[IngestGroupListResponse]: Ingest 템플릿 목록과 페이지네이션 정보
    """
    groups, total_items = await list_ingest_groups(
        session=session,
        page_num=pageNum,
        page_size=pageSize,
        sort_by=sort,
    )

    # 응답 데이터 변환
    items = [
        IngestGroupListItem(
            ingestNo=_bytes_to_uuid_str(group.ingest_group_no),
            name=group.name,
            isDefault=group.is_default,
        )
        for group in groups
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

    return BaseResponse[IngestGroupListResponse](
        status=200,
        code="OK",
        message="성공",
        isSuccess=True,
        result=Result(data=IngestGroupListResponse(data=items, pagination=pagination)),
    )


@router.get(
    "/ingest-templates/{ingestNo}",
    response_model=BaseResponse[IngestTemplateDetailResponse],
    summary="Ingest 템플릿 상세 조회 (관리자 전용)",
    description="Ingest 템플릿 상세 정보를 조회합니다. 관리자만 접근 가능합니다.",
)
async def get_ingest_template(
    ingestNo: str,
    x_user_role: str = Depends(check_role("ADMIN")),
    session: AsyncSession = Depends(get_db),
):
    """
    Ingest 템플릿 상세 조회

    현재 데이터베이스 스키마 제약으로 인해:
    - extractions는 단일 전략을 리스트로 반환합니다
    - denseEmbeddings는 단일 전략을 리스트로 반환합니다
    - spareEmbedding이 실제 저장된 메인 임베딩 전략입니다

    Args:
        ingestNo: Ingest 템플릿 ID (UUID)
        x_user_role: 사용자 역할 (헤더, 전역 security에서 자동 주입)
        session: 데이터베이스 세션

    Returns:
        BaseResponse[IngestTemplateDetailResponse]: 템플릿 상세 정보

    Raises:
        HTTPException 400: UUID 형식 오류
        HTTPException 404: Ingest 템플릿 또는 관련 전략을 찾을 수 없음
    """
    # 템플릿 조회
    ingest_group = await get_ingest_template_detail(
        session=session,
        ingest_no=ingestNo,
    )

    # 필수 관계 데이터 검증 (데이터 정합성 오류는 500)
    if not ingest_group.extraction_strategy:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="데이터 정합성 오류: 추출 전략이 누락되었습니다. 관리자에게 문의하세요."
        )
    if not ingest_group.chunking_strategy:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="데이터 정합성 오류: 청킹 전략이 누락되었습니다. 관리자에게 문의하세요."
        )
    if not ingest_group.embedding_strategy:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="데이터 정합성 오류: 임베딩 전략이 누락되었습니다. 관리자에게 문의하세요."
        )

    # Strategy 객체를 StrategyItem으로 변환하는 헬퍼 함수
    def strategy_to_item(strategy) -> StrategyItem:
        return StrategyItem(
            no=_bytes_to_uuid_str(strategy.strategy_no),
            name=strategy.name,
            description=strategy.description or "",
            parameters=strategy.parameter or {}
        )

    # 응답 데이터 변환
    # 현재 스키마 제약: 단일 전략을 리스트로 반환
    response_data = IngestTemplateDetailResponse(
        ingestNo=_bytes_to_uuid_str(ingest_group.ingest_group_no),
        name=ingest_group.name,
        isDefault=ingest_group.is_default,
        extractions=[strategy_to_item(ingest_group.extraction_strategy)],
        chunking=strategy_to_item(ingest_group.chunking_strategy),
        denseEmbeddings=[strategy_to_item(ingest_group.embedding_strategy)],
        spareEmbedding=strategy_to_item(ingest_group.embedding_strategy),
    )

    return BaseResponse[IngestTemplateDetailResponse](
        status=200,
        code="OK",
        message="성공",
        isSuccess=True,
        result=Result(data=response_data),
    )
