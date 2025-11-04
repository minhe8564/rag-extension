from __future__ import annotations

from typing import List
import uuid

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.schemas import BaseResponse
from ..schemas.file_category import FileCategoryListItem
from ..services.file_category import list_file_categories as list_file_categories_service


router = APIRouter(prefix="/files/categories", tags=["FileCategory"])


@router.get("/", response_model=BaseResponse[List[FileCategoryListItem]])
async def list_file_categories(
    session: AsyncSession = Depends(get_db),
):
    items: List[FileCategoryListItem] = await list_file_categories_service(session)

    return BaseResponse[List[FileCategoryListItem]](
        status=200,
        code="OK",
        message="문서 목록 조회에 성공하였습니다.",
        isSuccess=True,
        result={"data": items},
    )
