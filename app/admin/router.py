from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..database import get_db
from .models import RunPod
from .schemas import RunPodResponse, RunPodUpdate, RunPodUrlOnly

router = APIRouter(
    prefix="/admin",
    tags=["AI Admin - RunPod Management"]
)

@router.get(
    "/runpod",
    response_model=RunPodUrlOnly,
    summary="Get Runpod Url",
    description="현재 활성화된 RunPod URL을 조회합니다."
)
async def get_runpod_url(db: AsyncSession = Depends(get_db)):
    """
    현재 활성화된 RunPod URL 조회
    
    - 가장 최근에 등록된 RunPod URL을 반환합니다.
    - URL만 반환됩니다 (ID, 시간 정보 제외).
    """
    result = await db.execute(
        select(RunPod).order_by(RunPod.id.desc()).limit(1)
    )
    runpod = result.scalar_one_or_none()
    
    if not runpod:
        raise HTTPException(
            status_code=404, 
            detail="RunPod URL not found. Please set it first."
        )
    
    return runpod


@router.patch(
    "/runpod",
    status_code=204,
    summary="Update Runpod Url",
    description="RunPod URL을 업데이트합니다."
)
async def update_runpod_url(
    runpod_update: RunPodUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    RunPod URL 업데이트
    
    - 기존 URL이 있으면 업데이트, 없으면 새로 생성합니다.
    - 204 No Content를 반환합니다.
    """
    result = await db.execute(
        select(RunPod).order_by(RunPod.id.desc()).limit(1)
    )
    runpod = result.scalar_one_or_none()
    
    if runpod:
        runpod.api_url = runpod_update.api_url
    else:
        runpod = RunPod(api_url=runpod_update.api_url)
        db.add(runpod)
    
    await db.commit()
    
    return Response(status_code=204)


@router.post(
    "/runpod",
    status_code=201,
    summary="Create Runpod Url",
    description="새로운 RunPod URL을 생성합니다 (히스토리 유지)."
)
async def create_runpod_url(
    runpod_update: RunPodUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    새로운 RunPod URL 생성
    
    - 기존 URL을 유지하고 새로운 레코드를 추가합니다.
    - 히스토리 관리에 유용합니다.
    - 201 Created를 반환합니다 (응답 body 없음).
    """
    runpod = RunPod(api_url=runpod_update.api_url)
    db.add(runpod)
    
    await db.commit()
    
    return Response(status_code=201)


@router.get(
    "/runpod/history",
    response_model=list[RunPodResponse],
    summary="Get Runpod History",
    description="RunPod URL 변경 히스토리를 조회합니다."
)
async def get_runpod_history(
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """
    RunPod URL 변경 히스토리 조회
    
    - 최근 변경 내역을 시간 역순으로 조회합니다.
    - ID, URL, 생성/수정 시간을 모두 포함합니다.
    """
    result = await db.execute(
        select(RunPod).order_by(RunPod.id.desc()).limit(limit)
    )
    runpods = result.scalars().all()
    
    return runpods


@router.delete(
    "/runpod",
    status_code=204,
    summary="Delete Runpod Url",
    description="특정 URL의 RunPod를 삭제합니다."
)
async def delete_runpod_url(
    api_url: str,
    db: AsyncSession = Depends(get_db)
):
    """
    특정 RunPod URL 삭제
    
    - api_url 파라미터로 삭제할 URL을 지정합니다.
    - 일치하는 URL이 없으면 404 에러를 반환합니다.
    - 204 No Content를 반환합니다.
    
    Example:
        DELETE /api/admin/runpod?api_url=https://api.runpod.ai/v2/xxx
    """
    result = await db.execute(
        select(RunPod).where(RunPod.api_url == api_url)
    )
    runpod = result.scalar_one_or_none()
    
    if not runpod:
        raise HTTPException(
            status_code=404,
            detail=f"RunPod URL '{api_url}' not found"
        )
    
    await db.delete(runpod)
    await db.commit()
    
    return Response(status_code=204)


@router.delete(
    "/runpod/all",
    status_code=204,
    summary="Delete All Runpod Urls",
    description="모든 RunPod URL을 삭제합니다 (주의!)."
)
async def delete_all_runpod_urls(
    confirm: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """
    모든 RunPod URL 삭제 (위험!)
    
    - confirm=True를 반드시 설정해야 합니다.
    - 모든 히스토리가 삭제됩니다.
    
    Example:
        DELETE /api/admin/runpod/all?confirm=true
    """
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="Please set confirm=True to delete all RunPod URLs"
        )
    
    result = await db.execute(select(RunPod))
    runpods = result.scalars().all()
    
    if not runpods:
        raise HTTPException(
            status_code=404,
            detail="No RunPod URLs found"
        )
    
    for runpod in runpods:
        await db.delete(runpod)
    
    await db.commit()
    
    return Response(status_code=204)
