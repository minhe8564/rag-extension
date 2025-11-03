from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_session
from ..models.file_category import FileCategory
from ..schemas.file_category import FileCategoryOut


router = APIRouter(prefix="/file-categories", tags=["FileCategory"])


@router.get("/", response_model=List[FileCategoryOut])
async def list_file_categories(
    session: AsyncSession = Depends(get_session),
):
    stmt = select(FileCategory).order_by(FileCategory.name.asc())
    result = await session.execute(stmt)
    rows = result.scalars().all()
    # Convert PK to hex strings
    return [
        FileCategoryOut(
            file_category_no=row.pk_hex(),
            name=row.name,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
        for row in rows
    ]


@router.get("/{file_category_no}", response_model=FileCategoryOut)
async def get_file_category(
    file_category_no: str = Path(..., description="16-byte hex string"),
    session: AsyncSession = Depends(get_session),
):
    # Accept both 32-char hex and UUID with hyphens
    hex_str = file_category_no.replace("-", "").lower()
    if len(hex_str) != 32:
        raise HTTPException(status_code=400, detail="file_category_no must be 32-char hex")
    try:
        pk_bytes = bytes.fromhex(hex_str)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid hex for file_category_no")

    stmt = select(FileCategory).where(FileCategory.file_category_no == pk_bytes)
    result = await session.execute(stmt)
    row = result.scalars().first()
    if not row:
        raise HTTPException(status_code=404, detail="FileCategory not found")

    return FileCategoryOut(
        file_category_no=row.pk_hex(),
        name=row.name,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )

