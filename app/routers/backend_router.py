"""
Python Backend 프록시 라우터
gateway.ragextension.shop/be/*
"""
from fastapi import APIRouter, Request
from ..services.proxy_service import proxy_request
from ..core.settings import settings as app_settings

router = APIRouter(
    prefix="/be",
    tags=["Python Backend"]
)


@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
async def backend_proxy(request: Request, path: str):
    """
    /be/*로 들어오는 모든 요청을 python_backend_url로 프록시
    """
    return await proxy_request(
        request=request,
        target_url=app_settings.python_backend_url,
        path_prefix="/be"
    )

