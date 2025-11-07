"""
Ingest 템플릿 생성 라우터
"""
from typing import Any

from fastapi import APIRouter, Depends, status, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from ....core.database import get_db
from ....core.schemas import BaseResponse, Result
from ....core.check_role import check_role
from ..schemas.ingest import IngestTemplateCreateRequest, IngestTemplateCreateResponse
from ..services.ingest import create_ingest_template


router = APIRouter(prefix="/rag", tags=["RAG - Ingest Template Management"])
@router.post(
    "/ingest-templates",
    response_model=BaseResponse[IngestTemplateCreateResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Ingest 템플릿 생성 (관리자 전용)",
    description="새로운 Ingest 템플릿을 생성합니다. 관리자만 접근 가능합니다.",
)
async def create_ingest_template_endpoint(
    request: IngestTemplateCreateRequest,
    response: Response,
    x_user_role: str = Depends(check_role("ADMIN")),
    session: AsyncSession = Depends(get_db),
):
    """
    Ingest 템플릿 생성

    현재 데이터베이스 스키마 제약으로 인해:
    - extractions 리스트에서 첫 번째 항목만 사용됩니다
    - denseEmbeddings 리스트는 보조용으로만 받고, 저장 시 사용하지 않습니다
    - spareEmbedding이 메인 임베딩 전략으로 사용됩니다

    Args:
        request: Ingest 템플릿 생성 요청
        response: FastAPI Response 객체 (Location 헤더 설정용)
        x_user_role: 사용자 역할 (헤더, 전역 security에서 자동 주입)
        session: 데이터베이스 세션

    Returns:
        BaseResponse[IngestTemplateCreateResponse]: 생성된 템플릿 ID

    Raises:
        HTTPException 400: 전략을 찾을 수 없음
    """
    # 현재 스키마 제약: 첫 번째 항목만 사용
    first_extraction = request.extractions[0]

    # 템플릿 생성 (spareEmbedding을 메인 임베딩으로 사용)
    try:
        ingest_no = await create_ingest_template(
            session=session,
            name=request.name,
            is_default=request.isDefault,
            extraction_no=first_extraction.no,
            extraction_parameters=first_extraction.parameters or {},
            chunking_no=request.chunking.no,
            chunking_parameters=request.chunking.parameters or {},
            embedding_no=request.spareEmbedding.no,
            embedding_parameters=request.spareEmbedding.parameters or {},
        )
    except HTTPException:
        # 전역 예외 핸들러가 처리하도록 그대로 전파
        raise

    # Location 헤더 설정
    response.headers["Location"] = f"/rag/ingest-templates/{ingest_no}"

    return BaseResponse[IngestTemplateCreateResponse](
        status=201,
        code="CREATED",
        message="성공",
        isSuccess=True,
        result=Result(data=IngestTemplateCreateResponse(ingestNo=ingest_no)),
    )
