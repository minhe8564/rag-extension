from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class RequestContext(BaseModel):
    """Common request context extracted from headers.

    - userNo: UUID string from `x-user-uuid`
    - role: Optional role from `x-user-role`
    """

    userNo: str
    role: Optional[str] = None

