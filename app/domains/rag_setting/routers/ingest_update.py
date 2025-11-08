"""
Ingest 템플릿 수정 라우터
"""
import uuid

from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ....core.database import get_db
from ....core.schemas import BaseResponse, Result
from ....core.auth.check_role import check_role
from ..schemas.ingest import (
    IngestTemplateUpdateRequest,
    IngestTemplateDetailResponse,
    StrategyDetail,
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
        200: {
            "description": "Ingest 템플릿 수정에 성공하였습니다.",
            "content": {
                "application/json": {
                    "example": {
                        "status": 200,
                        "code": "OK",
                        "message": "Ingest 템플릿 수정 성공",
                        "isSuccess": True,
                        "result": { }
                    }
                }
            }
        }
    }       
)
async def update_ingest_template_endpoint(
    ingestNo: str,
    request: IngestTemplateUpdateRequest,
    x_user_role: str = Depends(check_role("ADMIN")),
    session: AsyncSession = Depends(get_db),
):
    """Ingest 템플릿 수정"""
    extractions_payload = [
        item.model_dump(exclude_none=True) for item in request.extractions
    ]
    chunking_payload = request.chunking.model_dump(exclude_none=True)
    dense_embeddings_payload = [
        item.model_dump(exclude_none=True) for item in request.denseEmbeddings
    ]
    spare_embedding_payload = request.spareEmbedding.model_dump(exclude_none=True)

    try:
        updated_ingest_group = await update_ingest_template(
            session=session,
            ingest_no=ingestNo,
            name=request.name,
            extractions=extractions_payload,
            chunking=chunking_payload,
            dense_embeddings=dense_embeddings_payload,
            spare_embedding=spare_embedding_payload,
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

    # Strategy 객체를 StrategyDetail로 변환하는 헬퍼 함수
    def strategy_to_item(strategy, parameters) -> StrategyDetail:
        return StrategyDetail(
            no=_bytes_to_uuid_str(strategy.strategy_no),
            code=strategy.code,
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

    spare_item = None
    dense_embedding_items = []

    for item in embedding_items:
        params = item.parameters or {}
        embedding_type = params.get("type")
        code = (item.code or "").upper()

        if embedding_type == "spare" or code == "EMB_SPARE":
            if spare_item is None:
                spare_item = item
            else:
                dense_embedding_items.append(item)
        elif embedding_type == "dense" or code == "EMB_DENSE":
            dense_embedding_items.append(item)
        else:
            dense_embedding_items.append(item)

    if spare_item is None and embedding_items:
        spare_item = embedding_items[0]
        dense_embedding_items = [
            item for item in embedding_items if item is not spare_item
        ]

    response_data = IngestTemplateDetailResponse(
        ingestNo=_bytes_to_uuid_str(updated_ingest_group.ingest_group_no),
        name=updated_ingest_group.name,
        isDefault=updated_ingest_group.is_default,
        extractions=extraction_items,
        chunking=strategy_to_item(updated_ingest_group.chunking_strategy, updated_ingest_group.chunking_parameter),
        denseEmbeddings=dense_embedding_items,
        spareEmbedding=spare_item,
    )

    return BaseResponse[IngestTemplateDetailResponse](
        status=200,
        code="OK",
        message="Ingest 템플릿 수정 성공",
        isSuccess=True,
        result={},
    )
