"""
Ingest 템플릿 수정 라우터
"""
import uuid

from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ....core.database import get_db
from ....core.schemas import BaseResponse, Result
from ....core.check_role import check_role
from ..schemas.ingest import (
    IngestTemplateUpdateRequest,
    IngestTemplateDetailResponse,
    StrategyItem,
)
from ..services.ingest import update_ingest_template


router = APIRouter(prefix="/rag", tags=["RAG - Ingest Template Management"])
def _bytes_to_uuid_str(b: bytes) -> str:
    """UUID 바이너리를 문자열로 변환"""
    try:
        return str(uuid.UUID(bytes=b))
    except Exception:
        return b.hex()


@router.put(
    "/ingest-templates/{ingestNo}",
    response_model=BaseResponse[IngestTemplateDetailResponse],
    summary="Ingest 템플릿 수정 (관리자 전용)",
    description="Ingest 템플릿을 수정합니다. 관리자만 접근 가능합니다.",
)
async def update_ingest_template_endpoint(
    ingestNo: str,
    request: IngestTemplateUpdateRequest,
    x_user_role: str = Depends(check_role("ADMIN")),
    session: AsyncSession = Depends(get_db),
):
    """
    Ingest 템플릿 수정

    현재 데이터베이스 스키마 제약으로 인해:
    - extractions 리스트에서 첫 번째 항목만 사용됩니다
    - denseEmbeddings 리스트는 보조용으로만 받고, 저장 시 사용하지 않습니다
    - spareEmbedding이 메인 임베딩 전략으로 사용됩니다

    Args:
        ingestNo: Ingest 템플릿 ID (UUID)
        request: Ingest 템플릿 수정 요청
        x_user_role: 사용자 역할 (헤더, 전역 security에서 자동 주입)
        session: 데이터베이스 세션

    Returns:
        BaseResponse[IngestTemplateDetailResponse]: 수정된 템플릿 정보

    Raises:
        HTTPException 400: 전략을 찾을 수 없음
        HTTPException 404: Ingest 템플릿을 찾을 수 없음
    """
    # 현재 스키마 제약: 첫 번째 항목만 사용
    first_extraction = request.extractions[0]

    # 템플릿 수정 (spareEmbedding을 메인 임베딩으로 사용)
    try:
        updated_ingest_group = await update_ingest_template(
            session=session,
            ingest_no=ingestNo,
            name=request.name,
            extraction_no=first_extraction.no,
            extraction_parameters=first_extraction.parameters or {},
            chunking_no=request.chunking.no,
            chunking_parameters=request.chunking.parameters or {},
            embedding_no=request.spareEmbedding.no,
            embedding_parameters=request.spareEmbedding.parameters or {},
            is_default=request.isDefault,
        )
    except HTTPException:
        # 전역 예외 핸들러가 처리하도록 그대로 전파
        raise

    # 필수 관계 데이터 검증 (데이터 정합성 오류는 500)
    if not updated_ingest_group.chunking_strategy:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="데이터 정합성 오류: 청킹 전략이 누락되었습니다. 관리자에게 문의하세요."
        )
    if not updated_ingest_group.extraction_groups:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="데이터 정합성 오류: 추출 전략 그룹이 누락되었습니다. 관리자에게 문의하세요."
        )
    if not updated_ingest_group.embedding_groups:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="데이터 정합성 오류: 임베딩 전략 그룹이 누락되었습니다. 관리자에게 문의하세요."
        )

    # Strategy 객체를 StrategyItem으로 변환하는 헬퍼 함수
    def strategy_to_item(strategy, parameters) -> StrategyItem:
        return StrategyItem(
            no=_bytes_to_uuid_str(strategy.strategy_no),
            name=strategy.name,
            description=strategy.description or "",
            parameters=parameters or {}
        )

    extraction_items = []
    for group in updated_ingest_group.extraction_groups:
        if not group.extraction_strategy:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="데이터 정합성 오류: 추출 전략이 누락되었습니다. 관리자에게 문의하세요."
            )
        extraction_items.append(
            strategy_to_item(group.extraction_strategy, group.extraction_parameter)
        )

    embedding_items = []
    for group in updated_ingest_group.embedding_groups:
        if not group.embedding_strategy:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="데이터 정합성 오류: 임베딩 전략이 누락되었습니다. 관리자에게 문의하세요."
            )
        embedding_items.append(
            strategy_to_item(group.embedding_strategy, group.embedding_parameter)
        )

    if not extraction_items or not embedding_items:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="데이터 정합성 오류: 필수 전략이 누락되었습니다. 관리자에게 문의하세요."
        )

    response_data = IngestTemplateDetailResponse(
        ingestNo=_bytes_to_uuid_str(updated_ingest_group.ingest_group_no),
        name=updated_ingest_group.name,
        isDefault=updated_ingest_group.is_default,
        extractions=extraction_items,
        chunking=strategy_to_item(updated_ingest_group.chunking_strategy, updated_ingest_group.chunking_parameter),
        denseEmbeddings=embedding_items,
        spareEmbedding=embedding_items[0],
    )

    return BaseResponse[IngestTemplateDetailResponse](
        status=200,
        code="OK",
        message="성공",
        isSuccess=True,
        result=Result(data=response_data),
    )
