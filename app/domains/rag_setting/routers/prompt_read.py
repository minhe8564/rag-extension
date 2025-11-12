"""
프롬프트 조회 라우터 (목록 + 상세)
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ....core.database import get_db
from ....core.schemas import BaseResponse, Result
from ....core.auth.check_role import check_role
from ..schemas.prompt import PromptListItem, PromptDetailResponse
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
    response_model=BaseResponse[Result[list[PromptListItem]]],
    summary="프롬프트 목록 조회",
    description="프롬프트 목록을 조회합니다. 관리자만 접근 가능합니다.",
    responses={
        200: {
            "description": "프롬프트 목록 조회에 성공하였습니다.",
            "content": {
                "application/json": {
                    "example": {
                        "status": 200,
                        "code": "OK",
                        "message": "성공",
                        "isSuccess": True,
                        "result": {
                            "data": [
                                {
                                    "promptNo": "9c6a37bc-ef9b-4776-928c-f45c9eb65934",
                                    "name": "샘플 사용자 프롬프트",
                                    "type": "user",
                                    "code": "PMT_USER",
                                    "description": "샘플 사용자 프롬프트",
                                    "content": "다음 지침을 따라 한국어로 간결하게 답하세요: (1) 아래 참고문서에서 근거를 먼저 찾고, (2) 문서 내용에 한해 답변하세요.\n질문: {{query}}\n참고문서: {{docs}}"
                                },
                                {
                                    "promptNo": "6bff6262-90a6-4eb1-bfc1-78bdd342c317",
                                    "name": "샘플 시스템 프롬프트",
                                    "type": "system",
                                    "code": "PMT_SYSTEM",
                                    "description": "샘플 시스템 프롬프트",
                                    "content": "당신은 유용한 RAG 어시스턴트입니다. 사용자의 언어(기본: 한국어)로 간결하게 답하고, 정확성을 최우선으로 하며, 모든 주장은 검색·조회된 출처에 근거해 제시하세요."
                                }
                            ]
                        }
                    }
                }
            }
        }
    }
)
async def get_prompts(
    x_user_role: str = Depends(check_role("ADMIN")),
    session: AsyncSession = Depends(get_db),
    prompt_type: str | None = Query(
        None,
        alias="type",
        description="프롬프트 유형 필터 (system 또는 user)",
    ),
):
    """
    프롬프트 목록 조회

    Args:
        x_user_role: 사용자 역할 (헤더, 전역 security에서 자동 주입)
        session: 데이터베이스 세션
        prompt_type: 필터링할 프롬프트 유형 (system 또는 user)

    Returns:
        BaseResponse: 프롬프트 목록
    """
    if prompt_type and prompt_type not in ("system", "user"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="지원하지 않는 프롬프트 유형입니다. (system, user만 허용)",
        )

    # 프롬프트 목록 조회
    prompts = await list_prompts(
        session=session,
        prompt_type=prompt_type,
    )

    # 응답 데이터 변환
    items = [
        PromptListItem(
            promptNo=_bytes_to_uuid_str(prompt.strategy_no),
            name=prompt.name,
            type=prompt.parameter.get("type", "system") if prompt.parameter else "system",
            code=prompt.code,
            description=prompt.description,
            content=prompt.parameter.get("content", "") if prompt.parameter else ""
        )
        for prompt in prompts
    ]

    return BaseResponse[Result[list[PromptListItem]]](
        status=200,
        code="OK",
        message="프롬프트 목록 조회에 성공하였습니다.",
        isSuccess=True,
        result=Result[list[PromptListItem]](data=items)
    )


@router.get(
    "/prompts/{promptNo}",
    response_model=BaseResponse[PromptDetailResponse],
    summary="프롬프트 상세 조회",
    description="특정 프롬프트의 상세 정보를 조회합니다. 관리자만 접근 가능합니다.",
    responses={
        200: {
            "description": "프롬프트 상세 조회에 성공하였습니다.",
            "content": {
                "application/json": {
                    "example": {
                    "status": 200,
                    "code": "OK",
                    "message": "성공",
                    "isSuccess": True,
                    "result": {
                            "promptNo": "6bff6262-90a6-4eb1-bfc1-78bdd342c317",
                            "name": "샘플 시스템 프롬프트",
                            "type": "system",
                            "code": "PMT_SYSTEM",
                            "description": "샘플 시스템 프롬프트",
                            "content": "당신은 유용한 RAG 어시스턴트입니다. 사용자의 언어(기본: 한국어)로 간결하게 답하고, 정확성을 최우선으로 하며, 모든 주장은 검색·조회된 출처에 근거해 제시하세요."
                        }
                    }
                }
            }
        }
    }
)
async def get_prompt_detail(
    promptNo: str,
    x_user_role: str = Depends(check_role("ADMIN")),
    session: AsyncSession = Depends(get_db)
):
    """
    프롬프트 상세 정보 조회

    Args:
        promptNo: 프롬프트 ID (UUID)
        x_user_role: 사용자 역할 (헤더, 전역 security에서 자동 주입)
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
        code=prompt.code,
        description=prompt.description,
        content=prompt.parameter.get("content", "") if prompt.parameter else ""
    )

    return BaseResponse[PromptDetailResponse](
        status=200,
        code="OK",
        message="프롬프트 상세 조회에 성공하였습니다.",
        isSuccess=True,
        result=detail
    )
