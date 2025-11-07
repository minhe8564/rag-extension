from __future__ import annotations

import uuid
import logging
from pathlib import Path
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import settings
from app.core.minio_client import remove_object

from ..models.file import File
from ..models.file_category import FileCategory
from app.domains.user.models.user import User


logger = logging.getLogger(__name__)


def _uuid_str_to_bytes(u: str, *, field_name: Optional[str] = None) -> bytes:
    try:
        return uuid.UUID(u).bytes
    except Exception:
        fn = field_name or "uuid"
        try:
            logger.warning("Invalid UUID for %s: %r", fn, u)
        except Exception:
            pass
        raise HTTPException(
            status_code=400,
            detail={
                "message": f"Invalid {fn} format (UUID required)",
                "field": fn,
            },
        )


def _bytes_to_uuid_str(b: bytes) -> str:
    try:
        return str(uuid.UUID(bytes=b))
    except Exception:
        return b.hex() if isinstance(b, (bytes, bytearray)) else str(b)


async def _get_offer_no_by_user(session: AsyncSession, user_no_bytes: bytes) -> str:
    stmt = select(User.offer_no).where(User.user_no == user_no_bytes)
    res = await session.execute(stmt)
    offer_no = res.scalar_one_or_none()
    if offer_no is None:
        raise HTTPException(status_code=400, detail="존재하지 않는 사용자입니다.")
    return offer_no


async def _ensure_category_exists(session: AsyncSession, category_no_bytes: bytes) -> None:
    stmt = select(FileCategory.file_category_no).where(FileCategory.file_category_no == category_no_bytes)
    res = await session.execute(stmt)
    if res.scalar_one_or_none() is None:
        raise HTTPException(status_code=400, detail="존재하지 않는 카테고리입니다.")


def _resolve_bucket(input_bucket: Optional[str], offer_no: str) -> tuple[str, bool]:
    # returns (bucket_name, should_create)
    # If explicit bucket is provided, use it as-is (ADMIN flow), creating if needed.
    if input_bucket:
        b = input_bucket.strip()
        lb = b.lower()
        if lb == "public":
            return (getattr(settings, "default_public_bucket", None) or "public"), False
        if lb == "hebees":
            return (getattr(settings, "default_hebees_bucket", None) or "hebees"), False
        return b, True
    # Otherwise use personal (offer_no) bucket (USER flow)
    return offer_no, True


def _build_presigned_key(category_no: str, filename: str) -> str:
    safe_name = Path(filename).name
    return f"{category_no}/{safe_name}"


def _split_name_ext(filename: str) -> tuple[str, str]:
    p = Path(filename).name
    stem = Path(p).stem
    ext = Path(p).suffix  # includes dot or empty
    return stem, ext


async def _handle_name_conflict(
    session: AsyncSession,
    *,
    bucket_name: str,
    category_no_bytes: bytes,
    original_name: str,
    policy: str,
    user_role: str | None = None,
) -> None:
    policy = (policy or "reject").lower()
    if policy not in {"reject", "overwrite"}:
        raise HTTPException(status_code=400, detail="onNameConflict 값이 올바르지 않습니다.")

    if policy == "reject":
        stmt = (
            select(File.file_no)
            .where(File.bucket == bucket_name)
            .where(File.file_category_no == category_no_bytes)
            .where(File.name == original_name)
        )
        res = await session.execute(stmt)
        if res.scalar_one_or_none() is not None:
            raise HTTPException(status_code=409, detail="해당 파일명은 이미 존재합니다.")
        return

    # overwrite: remove existing objects and rows with the same name
    stmt = (
        select(File)
        .where(File.bucket == bucket_name)
        .where(File.file_category_no == category_no_bytes)
        .where(File.name == original_name)
    )
    res = await session.execute(stmt)
    existing_rows = list(res.scalars().all())
    if existing_rows:
        # Reuse central deletion logic (includes vector cleanup if configured)
        from .delete import delete_file_entity
        for row in existing_rows:
            try:
                await delete_file_entity(session, file_row=row, user_role=user_role)
            except Exception as e:
                try:
                    logger.warning("Failed to delete existing file on overwrite: %s", e)
                except Exception:
                    pass
