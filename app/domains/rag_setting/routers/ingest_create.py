"""
Ingest 템플릿 생성 라우터
"""
from typing import Any

from fastapi import APIRouter, Depends, status, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from ....core.database import get_db
from ....core.schemas import BaseResponse, Result
from ....core.auth.check_role import check_role
from ..schemas.ingest import IngestTemplateCreateRequest, IngestTemplateCreateResponse
from ..services.ingest import create_ingest_template


router = APIRouter(prefix="/rag", tags=["RAG - Ingest Template Management"])
@router.post(
    "/ingest-templates",
    response_model=BaseResponse[IngestTemplateCreateResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Ingest 템플릿 생성 (관리자 전용)",
    description="새로운 Ingest 템플릿을 생성합니다. 관리자만 접근 가능합니다.",
    responses={
        "201": {
            "description": "Ingest 템플릿 생성 성공",
            "content": {
                "application/json": {
                    "example": {
                        "status": 201,
                        "code": "CREATED",
                        "message": "Ingest 템플릿 생성 성공",
                        "isSuccess": True,
                        "result": {
                            "data": {
                                "ingestNo": "92514bae-2bcf-479f-a549-1db3bb68a699"
                            }
                        }
                    }
                }
            }
        }
    }   
)
async def create_ingest_template_endpoint(
    request: IngestTemplateCreateRequest,
    response: Response,
    x_user_role: str = Depends(check_role("ADMIN")),
    session: AsyncSession = Depends(get_db),
):
    """Ingest 템플릿 생성"""
    extractions_payload = [
        item.model_dump(exclude_none=True) for item in request.extractions
    ]
    chunking_payload = request.chunking.model_dump(exclude_none=True)
    dense_embeddings_payload = [
        item.model_dump(exclude_none=True) for item in request.denseEmbeddings
    ]
    sparse_embedding_payload = request.sparseEmbedding.model_dump(exclude_none=True)

    try:
        ingest_no = await create_ingest_template(
            session=session,
            name=request.name,
            is_default=request.isDefault,
            extractions=extractions_payload,
            chunking=chunking_payload,
            dense_embeddings=dense_embeddings_payload,
            sparse_embedding=sparse_embedding_payload,
        )
    except HTTPException:
        # 전역 예외 핸들러가 처리하도록 그대로 전파
        raise

    # Location 헤더 설정
    response.headers["Location"] = f"/rag/ingest-templates/{ingest_no}"

    return BaseResponse[IngestTemplateCreateResponse](
        status=201,
        code="CREATED",
        message="Ingest 템플릿 생성 성공",
        isSuccess=True,
        result=IngestTemplateCreateResponse(ingestNo=ingest_no),
    )
