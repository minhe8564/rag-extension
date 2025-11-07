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

    extractions와 denseEmbeddings, spareEmbedding을 모두 별도 그룹 테이블에 저장합니다.

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
    # extractions 리스트를 dict 형태로 변환
    extractions = [
        {
            "no": ext.no,
            "name": "추출 전략",
            "parameters": ext.parameters or {}
        }
        for ext in request.extractions
    ]

    # embeddings 리스트 생성 (denseEmbeddings + spareEmbedding)
    embeddings = [
        {
            "no": emb.no,
            "name": "임베딩 전략",
            "parameters": emb.parameters or {}
        }
        for emb in request.denseEmbeddings
    ]
    # spareEmbedding 추가
    embeddings.append({
        "no": request.spareEmbedding.no,
        "name": "희소 임베딩 전략",
        "parameters": request.spareEmbedding.parameters or {}
    })

    # 템플릿 수정
    try:
        updated_ingest_group = await update_ingest_template(
            session=session,
            ingest_no=ingestNo,
            name=request.name,
            extractions=extractions,
            chunking_no=request.chunking.no,
            chunking_parameters=request.chunking.parameters or {},
            embeddings=embeddings,
            is_default=request.isDefault,
        )
    except HTTPException:
        # 전역 예외 핸들러가 처리하도록 그대로 전파
        raise

    # 필수 관계 데이터 검증
    if not updated_ingest_group.chunking_strategy:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="데이터 정합성 오류: 청킹 전략이 누락되었습니다. 관리자에게 문의하세요."
        )
    if not updated_ingest_group.extraction_groups:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="데이터 정합성 오류: 추출 전략이 누락되었습니다. 관리자에게 문의하세요."
        )
    if not updated_ingest_group.embedding_groups:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="데이터 정합성 오류: 임베딩 전략이 누락되었습니다. 관리자에게 문의하세요."
        )

    # 응답 데이터 변환 (스키마 메서드 사용)
    response_data = IngestTemplateDetailResponse.from_ingest_group(updated_ingest_group)

    return BaseResponse[IngestTemplateDetailResponse](
        status=200,
        code="OK",
        message="Ingest 템플릿 수정에 성공하였습니다.",
        isSuccess=True,
        result=Result(data=response_data),
    )
