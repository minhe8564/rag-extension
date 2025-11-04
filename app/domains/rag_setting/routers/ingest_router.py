from typing import Dict, Any, List
import math
import uuid

from fastapi import APIRouter, Depends, Query, Header, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import ValidationError

from ....core.database import get_db
from ....core.schemas import BaseResponse, Result
from ....core.check_role import check_role
from ....core.error_responses import admin_only_responses
from ..schemas.ingest import (
    IngestGroupListItem,
    IngestTemplateCreateRequest,
    IngestTemplateCreateResponse,
    InvalidInputError,
)
from ..schemas.strategy import PaginationInfo
from ..services.ingest import list_ingest_groups, create_ingest_template


router = APIRouter(prefix="/rag", tags=["RAG - Ingest Template Management"])


def _bytes_to_uuid_str(b: bytes) -> str:
    """UUID 바이너리를 문자열로 변환"""
    try:
        return str(uuid.UUID(bytes=b))
    except Exception:
        return b.hex()


@router.get(
    "/ingest-templates",
    response_model=BaseResponse[Dict[str, Any]],
    summary="Ingest 템플릿 목록 조회 (관리자 전용)",
    description="Ingest 템플릿 목록을 조회합니다. 관리자만 접근 가능합니다.",
    responses=admin_only_responses(),
)
async def get_ingest_templates(
    pageNum: int = Query(1, ge=1, description="페이지 번호"),
    pageSize: int = Query(20, ge=1, le=100, description="페이지 크기"),
    sort: str = Query("created_at", description="정렬 기준"),
    x_user_role: str = Depends(check_role("ADMIN")),
    x_user_uuid: str = Header(..., alias="x-user-uuid"),
    session: AsyncSession = Depends(get_db),
):
    """
    Ingest 템플릿 목록 조회

    Args:
        pageNum: 페이지 번호
        pageSize: 페이지 크기
        sort: 정렬 기준
        x_user_role: 사용자 역할 (헤더)
        x_user_uuid: 사용자 UUID (헤더)

    Returns:
        BaseResponse: Ingest 템플릿 목록과 페이지네이션 정보
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
            isDefault=group.is_default,
            extractionStrategy={
                "strategyNo": _bytes_to_uuid_str(group.extraction_strategy_no),
                "name": group.extraction_strategy.name if group.extraction_strategy else "",
                "parameter": group.extraction_parameter,
            },
            chunkingStrategy={
                "strategyNo": _bytes_to_uuid_str(group.chunking_strategy_no),
                "name": group.chunking_strategy.name if group.chunking_strategy else "",
                "parameter": group.chunking_parameter,
            },
            embeddingStrategy={
                "strategyNo": _bytes_to_uuid_str(group.embedding_strategy_no),
                "name": group.embedding_strategy.name if group.embedding_strategy else "",
                "parameter": group.embedding_parameter,
            },
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

    return BaseResponse[Dict[str, Any]](
        status=200,
        code="OK",
        message="Ingest 템플릿 목록 조회에 성공하였습니다.",
        isSuccess=True,
        result=Result(data={"data": items, "pagination": pagination}),
    )


@router.post(
    "/ingest-templates",
    response_model=BaseResponse[IngestTemplateCreateResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Ingest 템플릿 생성 (관리자 전용)",
    description="새로운 Ingest 템플릿을 생성합니다. 관리자만 접근 가능합니다.",
    responses={
        **admin_only_responses(),
        201: {
            "description": "템플릿 생성 성공",
            "headers": {
                "Location": {
                    "description": "생성된 리소스의 URI",
                    "schema": {"type": "string"}
                }
            }
        },
        400: {
            "description": "잘못된 요청 (파라미터 누락 또는 유효하지 않은 전략 ID)",
            "content": {
                "application/json": {
                    "example": {
                        "status": 400,
                        "code": "INVALID_INPUT",
                        "message": "파라미터가 누락되었습니다.",
                        "isSuccess": False,
                        "result": {
                            "data": {
                                "missing": ["name", "chunking", "chunking.no"]
                            }
                        }
                    }
                }
            }
        }
    },
)
async def create_ingest_template_endpoint(
    request: IngestTemplateCreateRequest,
    response: Response,
    x_user_role: str = Depends(check_role("ADMIN")),
    x_user_uuid: str = Header(..., alias="x-user-uuid"),
    session: AsyncSession = Depends(get_db),
):
    """
    Ingest 템플릿 생성

    현재 데이터베이스 스키마 제약으로 인해:
    - extractions 리스트에서 첫 번째 항목만 사용됩니다
    - denseEmbeddings 리스트에서 첫 번째 항목만 사용됩니다
    - spareEmbedding이 메인 임베딩 전략으로 사용됩니다

    Args:
        request: Ingest 템플릿 생성 요청
        response: FastAPI Response 객체 (Location 헤더 설정용)
        x_user_role: 사용자 역할 (헤더)
        x_user_uuid: 사용자 UUID (헤더)
        session: 데이터베이스 세션

    Returns:
        BaseResponse[IngestTemplateCreateResponse]: 생성된 템플릿 ID
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
                    "data": {
                        "missing": missing_fields
                    }
                }
            }
        )

    # 현재 스키마 제약: 첫 번째 항목만 사용
    first_extraction = request.extractions[0]
    first_dense_embedding = request.denseEmbeddings[0]

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
    except HTTPException as e:
        # 전략을 찾을 수 없는 경우
        if e.status_code == status.HTTP_400_BAD_REQUEST:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": 400,
                    "code": "INVALID_INPUT",
                    "message": str(e.detail),
                    "isSuccess": False,
                    "result": {
                        "data": {}
                    }
                }
            )
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
