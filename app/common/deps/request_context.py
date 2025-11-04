from __future__ import annotations

from typing import Optional

from fastapi import Header

from ..schemas.request import RequestContext


def get_request_context(
    x_user_uuid: str = Header(..., alias="x-user-uuid"),
    x_user_role: Optional[str] = Header(None, alias="x-user-role"),
) -> RequestContext:
    """Extracts common auth/user context from headers.

    Headers:
    - x-user-uuid: required UUID string identifying the user
    - x-user-role: optional role string (e.g., USER, ADMIN)
    """
    return RequestContext(userNo=x_user_uuid, role=x_user_role)

