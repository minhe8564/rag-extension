from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..common.auth.dependencies import require_admin
from ..common.auth.models import UserInfo
from ..database import get_db
from .models import BaseURL
from .schemas import BaseURLResponse, BaseURLCreate, BaseURLUpdate, BaseURLSimple
from ..common.cache.service_url_cache import service_url_cache

router = APIRouter(
    prefix="/admin",
    tags=["AI Admin - Base URL Management"]
)

@router.get(
    "/base-urls",
    response_model=list[BaseURLSimple],
    summary="Get All Base URLs",
    description="모든 서비스의 Base URL을 조회합니다."
)
async def get_all_base_urls(
    db: AsyncSession = Depends(get_db),
    current_user: UserInfo = Depends(require_admin)
):
    """모든 Base URL 조회"""
    result = await db.execute(select(BaseURL))
    base_urls = result.scalars().all()
    return base_urls

@router.get(
    "/base-urls/{service_name}",
    response_model=BaseURLSimple,
    summary="Get Base URL by Service Name",
    description="특정 서비스의 Base URL을 조회합니다."
)
async def get_base_url(
    service_name: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserInfo = Depends(require_admin)
):
    """특정 서비스 Base URL 조회"""
    result = await db.execute(select(BaseURL).where(BaseURL.service_name == service_name))
    base_url = result.scalar_one_or_none()
    
    if not base_url:
        raise HTTPException(status_code=404, detail=f"Base URL for service '{service_name}' not found")
    
    return base_url

@router.post(
    "/base-urls",
    status_code=204,
    summary="Create Base URL",
    description="새로운 서비스의 Base URL을 생성합니다."
)
async def create_base_url(
    base_url: BaseURLCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserInfo = Depends(require_admin)
):
    """새 Base URL 생성"""
    # 중복 확인
    result = await db.execute(select(BaseURL).where(BaseURL.service_name == base_url.service_name))
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(status_code=400, detail=f"Base URL for service '{base_url.service_name}' already exists")
    
    db_base_url = BaseURL(**base_url.dict())
    db.add(db_base_url)
    await db.commit()
    
    # 캐시 갱신
    await service_url_cache.refresh_cache()
    
    return Response(status_code=204)

@router.patch(
    "/base-urls/{service_name}",
    status_code=204,
    summary="Update Base URL",
    description="특정 서비스의 Base URL을 수정합니다."
)
async def update_base_url(
    service_name: str,
    base_url_update: BaseURLUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UserInfo = Depends(require_admin)
):
    """Base URL 수정"""
    result = await db.execute(select(BaseURL).where(BaseURL.service_name == service_name))
    base_url = result.scalar_one_or_none()
    
    if not base_url:
        raise HTTPException(status_code=404, detail=f"Base URL for service '{service_name}' not found")
    
    update_data = base_url_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(base_url, field, value)
    
    await db.commit()
    
    # 캐시 갱신
    await service_url_cache.refresh_cache()
    
    return Response(status_code=204)

@router.delete(
    "/base-urls/{service_name}",
    status_code=204,
    summary="Delete Base URL",
    description="특정 서비스의 Base URL을 삭제합니다."
)
async def delete_base_url(
    service_name: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserInfo = Depends(require_admin)
):
    """Base URL 삭제"""
    result = await db.execute(select(BaseURL).where(BaseURL.service_name == service_name))
    base_url = result.scalar_one_or_none()
    
    if not base_url:
        raise HTTPException(status_code=404, detail=f"Base URL for service '{service_name}' not found")
    
    await db.delete(base_url)
    await db.commit()
    
    # 캐시 갱신
    await service_url_cache.refresh_cache()
    
    return Response(status_code=204)