from typing import Dict, Any, List
import math
import uuid

from fastapi import APIRouter, Depends, Query, Header, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import ValidationError

from ....core.database import get_db
from ....core.schemas import BaseResponse, Result
from ....core.check_role import check_role
from ....core.error_responses import (
    admin_only_responses,
    unauthorized_error_response,
    forbidden_error_response,
    invalid_input_error_response,
    not_found_template_response,
)
from ..schemas.ingest import (
    IngestGroupListItem,
    IngestGroupListResponse,
    IngestTemplateCreateRequest,
    IngestTemplateCreateResponse,
    IngestTemplateDetailResponse,
    IngestTemplateUpdateRequest,
    InvalidInputError,
    StrategyItem,
)
from ..schemas.strategy import PaginationInfo
from ..services.ingest import list_ingest_groups, create_ingest_template, get_ingest_template_detail, update_ingest_template, delete_ingest_template


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
    responses=admin_only_responses(),
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
        400: invalid_input_error_response(["name", "chunking", "chunking.no"]),
    },
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
    - denseEmbeddings 리스트에서 첫 번째 항목만 사용됩니다
    - spareEmbedding이 메인 임베딩 전략으로 사용됩니다

    Args:
        request: Ingest 템플릿 생성 요청
        response: FastAPI Response 객체 (Location 헤더 설정용)
        x_user_role: 사용자 역할 (헤더, 전역 security에서 자동 주입)
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


@router.get(
    "/ingest-templates/{ingestNo}",
    response_model=BaseResponse[IngestTemplateDetailResponse],
    summary="Ingest 템플릿 상세 조회 (관리자 전용)",
    description="Ingest 템플릿 상세 정보를 조회합니다. 관리자만 접근 가능합니다.",
    responses={
        **admin_only_responses(),
        400: invalid_input_error_response(["ingestNo"]),
        404: not_found_template_response(),
    },
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
    """
    # 템플릿 조회
    ingest_group = await get_ingest_template_detail(
        session=session,
        ingest_no=ingestNo,
    )

    # 필수 관계 데이터 검증
    if not ingest_group.extraction_strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="추출 전략을 찾을 수 없습니다. 데이터 정합성을 확인해주세요."
        )
    if not ingest_group.chunking_strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="청킹 전략을 찾을 수 없습니다. 데이터 정합성을 확인해주세요."
        )
    if not ingest_group.embedding_strategy:
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
        BaseResponse: 수정 성공 응답
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


@router.delete(
    "/ingest-templates/{ingestNo}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Ingest 템플릿 삭제 (관리자 전용)",
    description="Ingest 템플릿을 삭제합니다. 관리자만 접근 가능합니다.",
    responses={
        **admin_only_responses(),
        204: {"description": "템플릿 삭제 성공 (응답 본문 없음)"},
    },
)
async def delete_ingest_template_endpoint(
    ingestNo: str,
    x_user_role: str = Depends(check_role("ADMIN")),
    session: AsyncSession = Depends(get_db),
):
    """
    Ingest 템플릿 삭제

    Args:
        ingestNo: Ingest 템플릿 ID (UUID)
        x_user_role: 사용자 역할 (헤더, 전역 security에서 자동 주입)
        session: 데이터베이스 세션

    Returns:
        204 No Content (응답 본문 없음)
    """
    await delete_ingest_template(
        session=session,
        ingest_no=ingestNo,
    )

    # 204 No Content는 응답 본문이 없음
    return Response(status_code=status.HTTP_204_NO_CONTENT)
