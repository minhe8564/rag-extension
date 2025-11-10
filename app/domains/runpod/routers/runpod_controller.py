from __future__ import annotations

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.schemas import BaseResponse, Result
from app.core.auth.check_role import check_role
from ..services.runpod_service import (
    create_runpod as create_runpod_service,
    get_all_runpods,
    update_runpod_by_name as update_runpod_by_name_service,
    bytes_to_hex,
)
from ..repositories.runpod_repository import RunpodRepository
from ..schemas.request.create_request import RunpodCreateRequest
from ..schemas.request.update_request import RunpodUpdateRequest
from ..schemas.response.runpod_response import RunpodResponse, RunpodListItem


router = APIRouter(prefix="/runpods", tags=["Runpod"])


@router.post("", response_model=BaseResponse[RunpodResponse], status_code=201)
async def create_runpod(
    request: RunpodCreateRequest,
    x_user_role: str = Depends(check_role("ADMIN")),
    session: AsyncSession = Depends(get_db),
):
    saved_runpod = await create_runpod_service(session, request)
    
    response_data = RunpodResponse(
        runpodNo=bytes_to_hex(saved_runpod.runpod_no),
        name=saved_runpod.name,
        address=saved_runpod.address,
        createdAt=saved_runpod.created_at,
        updatedAt=saved_runpod.updated_at,
    )
    
    return BaseResponse[RunpodResponse](
        status=201,
        code="CREATED",
        message="Runpod가 생성되었습니다.",
        isSuccess=True,
        result=Result(data=response_data),
    )


@router.get("", response_model=BaseResponse[List[RunpodListItem]])
async def get_runpods(
    x_user_role: str = Depends(check_role("ADMIN")),
    session: AsyncSession = Depends(get_db),
):
    runpods = await get_all_runpods(session)
    
    response_data = [
        RunpodListItem(
            runpodNo=bytes_to_hex(runpod.runpod_no),
            name=runpod.name,
            address=runpod.address,
            createdAt=runpod.created_at,
            updatedAt=runpod.updated_at,
        )
        for runpod in runpods
    ]
    
    return BaseResponse[List[RunpodListItem]](
        status=200,
        code="SUCCESS",
        message="Runpod 목록 조회 성공",
        isSuccess=True,
        result=Result(data=response_data),
    )


@router.get("/by-name/{name}", response_model=BaseResponse[RunpodResponse])
async def get_runpod_by_name(
    name: str,
    x_user_role: str = Depends(check_role("ADMIN")),
    session: AsyncSession = Depends(get_db),
):
    runpod = await RunpodRepository.find_by_name(session, name)
    
    if not runpod:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Runpod를 찾을 수 없습니다."
        )
    
    response_data = RunpodResponse(
        runpodNo=bytes_to_hex(runpod.runpod_no),
        name=runpod.name,
        address=runpod.address,
        createdAt=runpod.created_at,
        updatedAt=runpod.updated_at,
    )
    
    return BaseResponse[RunpodResponse](
        status=200,
        code="SUCCESS",
        message="Runpod 조회 성공",
        isSuccess=True,
        result=Result(data=response_data),
    )


@router.put("/by-name/{name}", response_model=BaseResponse[RunpodResponse])
async def update_runpod_by_name(
    name: str,
    request: RunpodUpdateRequest,
    x_user_role: str = Depends(check_role("ADMIN")),
    session: AsyncSession = Depends(get_db),
):
    try:
        updated_runpod = await update_runpod_by_name_service(session, name, request)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    
    response_data = RunpodResponse(
        runpodNo=bytes_to_hex(updated_runpod.runpod_no),
        name=updated_runpod.name,
        address=updated_runpod.address,
        createdAt=updated_runpod.created_at,
        updatedAt=updated_runpod.updated_at,
    )
    
    return BaseResponse[RunpodResponse](
        status=200,
        code="SUCCESS",
        message="Runpod가 수정되었습니다.",
        isSuccess=True,
        result=Result(data=response_data),
    )


@router.delete("/by-name/{name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_runpod_by_name(
    name: str,
    x_user_role: str = Depends(check_role("ADMIN")),
    session: AsyncSession = Depends(get_db),
):
    runpod = await RunpodRepository.find_by_name(session, name)
    
    if not runpod:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Runpod를 찾을 수 없습니다."
        )
    
    await RunpodRepository.delete(session, runpod)
    
    return None

