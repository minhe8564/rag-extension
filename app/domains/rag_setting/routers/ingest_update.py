"""
Ingest 템플릿 수정 라우터
"""
import uuid

from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ....core.database import get_db
from ....core.schemas import BaseResponse, Result
from ....core.check_role import check_role
from ....core.error_responses import (
    admin_only_responses,
    invalid_input_error_response,
    not_found_template_response,
)
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
    responses={
        **admin_only_responses(),
        400: invalid_input_error_response(["name", "chunking", "chunking.no"]),
        404: not_found_template_response(),
    },
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
    - denseEmbeddings 리스트에서 첫 번째 항목만 사용됩니다
    - spareEmbedding이 메인 임베딩 전략으로 사용됩니다

    Args:
        ingestNo: Ingest 템플릿 ID (UUID)
        request: Ingest 템플릿 수정 요청
        x_user_role: 사용자 역할 (헤더, 전역 security에서 자동 주입)
        session: 데이터베이스 세션

    Returns:
        BaseResponse[IngestTemplateDetailResponse]: 수정된 템플릿 정보

    Raises:
        HTTPException 400: 필수 파라미터 누락 또는 전략을 찾을 수 없음
        HTTPException 404: Ingest 템플릿을 찾을 수 없음
    """
    # 필수 필드 검증
    missing_fields = []

    if not request.name:
        missing_fields.append("name")
    if not request.extractions or len(request.extractions) == 0:
        missing_fields.append("extractions")
    if not request.chunking:
        missing_fields.append("chunking")
    if not request.chunking or not request.chunking.no:
        missing_fields.append("chunking.no")
    if not request.denseEmbeddings or len(request.denseEmbeddings) == 0:
        missing_fields.append("denseEmbeddings")
    if not request.spareEmbedding:
        missing_fields.append("spareEmbedding")
    if not request.spareEmbedding or not request.spareEmbedding.no:
        missing_fields.append("spareEmbedding.no")

    if missing_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "status": 400,
                "code": "INVALID_INPUT",
                "message": "파라미터가 누락되었습니다.",
                "isSuccess": False,
                "result": {
                    "missing": missing_fields
                }
            }
        )

    # 현재 스키마 제약: 첫 번째 항목만 사용
    first_extraction = request.extractions[0]
    first_dense_embedding = request.denseEmbeddings[0]

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
        )
    except HTTPException as e:
        # 전략을 찾을 수 없거나 템플릿을 찾을 수 없는 경우
        if e.status_code == status.HTTP_400_BAD_REQUEST:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": 400,
                    "code": "INVALID_INPUT",
                    "message": str(e.detail),
                    "isSuccess": False,
                    "result": {}
                }
            )
        elif e.status_code == status.HTTP_404_NOT_FOUND:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "status": 404,
                    "code": "NOT_FOUND",
                    "message": str(e.detail),
                    "isSuccess": False,
                    "result": {}
                }
            )
        raise

    # 필수 관계 데이터 검증
    if not updated_ingest_group.extraction_strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="추출 전략을 찾을 수 없습니다. 데이터 정합성을 확인해주세요."
        )
    if not updated_ingest_group.chunking_strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="청킹 전략을 찾을 수 없습니다. 데이터 정합성을 확인해주세요."
        )
    if not updated_ingest_group.embedding_strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="임베딩 전략을 찾을 수 없습니다. 데이터 정합성을 확인해주세요."
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
    response_data = IngestTemplateDetailResponse(
        ingestNo=_bytes_to_uuid_str(updated_ingest_group.ingest_group_no),
        name=updated_ingest_group.name,
        isDefault=updated_ingest_group.is_default,
        extractions=[strategy_to_item(updated_ingest_group.extraction_strategy)],
        chunking=strategy_to_item(updated_ingest_group.chunking_strategy),
        denseEmbeddings=[strategy_to_item(updated_ingest_group.embedding_strategy)],
        spareEmbedding=strategy_to_item(updated_ingest_group.embedding_strategy),
    )

    return BaseResponse[IngestTemplateDetailResponse](
        status=200,
        code="OK",
        message="성공",
        isSuccess=True,
        result=Result(data=response_data),
    )
