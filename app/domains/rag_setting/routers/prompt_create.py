"""
프롬프트 생성 라우터
"""
from fastapi import APIRouter, Depends, HTTPException, status, Header, Response
from sqlalchemy.ext.asyncio import AsyncSession

from ....core.database import get_db
from ....core.schemas import BaseResponse, Result
from ....core.check_role import check_role
from ....core.error_responses import admin_only_responses, conflict_error_response, invalid_input_error_response
from ..schemas.prompt import PromptCreateRequest, PromptCreateResponse
from ..services.prompt_create import create_prompt


router = APIRouter(prefix="/rag", tags=["RAG - Prompt Management"])


@router.post(
    "/prompts",
    response_model=BaseResponse[PromptCreateResponse],
    status_code=status.HTTP_201_CREATED,
    summary="프롬프트 생성",
    description="프롬프트를 생성합니다. 관리자만 접근 가능합니다.",
    responses={
        201: {
            "description": "프롬프트 생성 성공",
            "headers": {
                "Location": {
                    "description": "생성된 프롬프트 리소스의 URI",
                    "schema": {"type": "string"}
                }
            }
        },
        **admin_only_responses(),
        400: invalid_input_error_response(["name", "type", "content"]),
        409: conflict_error_response("프롬프트"),
    }
)
async def create_prompt_endpoint(
    request: PromptCreateRequest,
    response: Response,
    x_user_role: str = Depends(check_role("ADMIN")),
    session: AsyncSession = Depends(get_db),
):
    """
    프롬프트 생성

    Args:
        request: 프롬프트 생성 요청 데이터
        response: FastAPI Response 객체 (Location 헤더 설정용)
        x_user_role: 사용자 역할 (헤더, 전역 security에서 자동 주입)
        session: 데이터베이스 세션

    Returns:
        BaseResponse[PromptCreateResponse]: 생성된 프롬프트 정보

    Raises:
        HTTPException 400: 필수 파라미터 누락 또는 유효성 검증 실패
        HTTPException 409: 동일한 이름의 프롬프트 존재
    """
    # 프롬프트 생성
    prompt_no = await create_prompt(
        session=session,
        name=request.name,
        prompt_type=request.type,
        description=request.description,
        content=request.content
    )

    # Location 헤더 설정
    response.headers["Location"] = f"/rag/prompts/{prompt_no}"

    # 응답 반환
    return BaseResponse[PromptCreateResponse](
        status=201,
        code="CREATED",
        message="프롬프트 생성에 성공하였습니다.",
        isSuccess=True,
        result=Result(data=PromptCreateResponse(promptNo=prompt_no))
    )
