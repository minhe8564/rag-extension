from __future__ import annotations

from fastapi import APIRouter, Depends, Request, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.core.database import get_db
from app.core.schemas import BaseResponse
from ..repositories.file_repository import FileRepository
from ....core.utils.uuid_utils import _get_offer_no_by_user
from ..services.delete import delete_file_entity


router = APIRouter(prefix="/files", tags=["File"])


@router.delete("/{fileNo}", response_model=BaseResponse[dict])
async def delete_file(
    fileNo: str,
    http_request: Request,
    session: AsyncSession = Depends(get_db),
):
    x_user_role = http_request.headers.get("x-user-role")
    x_user_uuid = http_request.headers.get("x-user-uuid")
    if not x_user_role or not x_user_uuid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="x-user-role/x-user-uuid headers required")

    try:
        file_no_bytes = uuid.UUID(fileNo).bytes
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid fileNo format (UUID required)")

    file_rec = await FileRepository.find_by_file_no(session, file_no_bytes)
    if not file_rec:
        raise HTTPException(status_code=404, detail="File not found")

    # Permission check: non-ADMIN can only delete their offer's file
    role_upper = (x_user_role or "").upper()
    if role_upper != "ADMIN":
        try:
            user_no_bytes = uuid.UUID(x_user_uuid).bytes
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid x-user-uuid format (UUID required)")
        offer_no = await _get_offer_no_by_user(session, user_no_bytes)
        if file_rec.offer_no != offer_no:
            raise HTTPException(status_code=403, detail="Forbidden: file does not belong to your offer")

    # Perform deletion (MinIO -> vector cleanup -> DB)
    await delete_file_entity(session, file_row=file_rec, user_role=role_upper)
    await session.commit()

    return BaseResponse[dict](
        status=200,
        code="OK",
        message="파일 삭제 완료",
        isSuccess=True,
        result={"data": {
            "fileNo": fileNo, 
            "name" : file_rec.name,
            "deleted": True
            }
        },
    )

