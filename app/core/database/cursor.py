from datetime import datetime
from fastapi import Query
from typing import Optional

from pydantic import BaseModel


class CursorParams(BaseModel):
    cursorCreatedAt: Optional[datetime] = None
    cursorId: Optional[str] = None
    
    
async def get_cursor_params(
    cursorCreatedAt: Optional[datetime] = Query(None, description="커서 기준 생성 시간"),
    cursorId: Optional[str] = Query(None, description="커서 기준 ID"),
) -> CursorParams:
    return CursorParams(cursorCreatedAt=cursorCreatedAt, cursorId=cursorId)