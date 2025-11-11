from pydantic import BaseModel
from typing import Optional


class QueryProcessV2Request(BaseModel):
    """Query /process V2 요청 스키마 (userNo는 헤더 x-user-uuid에서 수신)"""
    llmNo: str
    sessionNo: str
    query: str


