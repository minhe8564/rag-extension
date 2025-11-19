"""
이미지 생성 API 라우터
HTTP 요청/응답 처리 및 라우팅
"""
from fastapi import APIRouter, Depends, Header, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
import logging
from app.core.utils.timezone_utils import now_kst

from app.core.database import get_db
from app.core.auth.check_role import check_role
from app.core.schemas import BaseResponse
from ..schemas.image_request import ImageGenerateRequest
from ..schemas.image_regenerate_request import ImageRegenerateRequest
from ..schemas.image_generate_response import ImageGenerateResponse
from ..schemas.image_response import ImageResponse
from ..services.image_service import ImageService
from ..services.minio_service import MinIOService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/images",
    tags=["Images"]
)


def get_minio_service() -> MinIOService:
    """MinIOService 의존성 주입"""
    return MinIOService()


def get_image_service(
    minio_service: MinIOService = Depends(get_minio_service)
) -> ImageService:
    """ImageService 의존성 주입"""
    return ImageService(minio_service)


@router.post("/generate", response_model=BaseResponse[ImageGenerateResponse])
async def generate_image(
    request: ImageGenerateRequest,
    x_user_role: str = Depends(check_role("USER", "ADMIN")),
    x_user_uuid: str = Header(..., alias="x-user-uuid"),
    image_service: ImageService = Depends(get_image_service),
    db: AsyncSession = Depends(get_db)
):
    try:
        generated_images = await image_service.generate_image(
            request=request,
            user_uuid=x_user_uuid,
            db=db
        )
        
        if not generated_images:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="이미지 생성에 실패했습니다."
            )
        
        image_data = ImageGenerateResponse(
            status="success",
            images=generated_images,
            created_at=now_kst()
        )
        
        return BaseResponse[ImageGenerateResponse](
            status=200,
            code="OK",
            message="이미지 생성에 성공하였습니다.",
            isSuccess=True,
            result={"data": image_data},
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"이미지 생성 중 비즈니스 로직 오류: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"이미지 생성 중 오류 발생: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"이미지 생성 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/regenerate", response_model=BaseResponse[ImageGenerateResponse])
async def regenerate_image(
    request: ImageRegenerateRequest,
    x_user_role: str = Depends(check_role("USER", "ADMIN")),
    x_user_uuid: str = Header(..., alias="x-user-uuid"),
    image_service: ImageService = Depends(get_image_service),
    db: AsyncSession = Depends(get_db)
):
    try:
        generated_images = await image_service.regenerate_image(
            request=request,
            user_uuid=x_user_uuid,
            db=db
        )
        
        if not generated_images:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="이미지 재생성에 실패했습니다."
            )
        
        image_data = ImageGenerateResponse(
            status="success",
            images=generated_images,
            created_at=now_kst()
        )
        
        return BaseResponse[ImageGenerateResponse](
            status=200,
            code="OK",
            message="이미지 재생성에 성공하였습니다.",
            isSuccess=True,
            result={"data": image_data},
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"이미지 재생성 중 비즈니스 로직 오류: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"이미지 재생성 중 오류 발생: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"이미지 재생성 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("", response_model=BaseResponse[List[ImageResponse]])
async def get_user_images(
    x_user_role: str = Depends(check_role("USER", "ADMIN")),
    x_user_uuid: str = Header(..., alias="x-user-uuid"),
    limit: int = Query(default=20, ge=1, le=100, description="페이지당 항목 수"),
    offset: int = Query(default=0, ge=0, description="건너뛸 항목 수"),
    image_service: ImageService = Depends(get_image_service),
    db: AsyncSession = Depends(get_db)
):
    try:
        image_responses = await image_service.get_images_by_user_uuid(
            user_uuid=x_user_uuid,
            db=db,
            limit=limit,
            offset=offset
        )
        
        return BaseResponse[List[ImageResponse]](
            status=200,
            code="OK",
            message="이미지 목록 조회에 성공하였습니다.",
            isSuccess=True,
            result={"data": image_responses},
        )
        
    except ValueError as e:
        logger.error(f"이미지 목록 조회 중 비즈니스 로직 오류: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"이미지 목록 조회 중 오류 발생: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"이미지 목록 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/{image_id}", response_model=BaseResponse[ImageResponse])
async def get_image(
    image_id: str,
    _: str = Depends(check_role("USER", "ADMIN")),
    image_service: ImageService = Depends(get_image_service),
    db: AsyncSession = Depends(get_db)
):
    try:
        image_response = await image_service.get_image_by_id(image_id, db)
        
        if not image_response:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="이미지를 찾을 수 없습니다."
            )
        
        return BaseResponse[ImageResponse](
            status=200,
            code="OK",
            message="이미지 조회에 성공하였습니다.",
            isSuccess=True,
            result={"data": image_response},
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"이미지 조회 중 오류 발생: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"이미지 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.delete("/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_image(
    image_id: str,
    x_user_role: str = Depends(check_role("USER", "ADMIN")),
    x_user_uuid: str = Header(..., alias="x-user-uuid"),
    image_service: ImageService = Depends(get_image_service),
    db: AsyncSession = Depends(get_db)
):
    try:
        await image_service.delete_image(
            image_id=image_id,
            user_uuid=x_user_uuid,
            db=db
        )
        return None
        
    except ValueError as e:
        logger.error(f"이미지 삭제 중 비즈니스 로직 오류: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"이미지 삭제 중 오류 발생: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"이미지 삭제 중 오류가 발생했습니다: {str(e)}"
        )

