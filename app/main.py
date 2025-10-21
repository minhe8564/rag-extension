from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from . import __version__, __title__, __description__
from .config import settings
from .common.auth.middleware import jwt_auth_middleware
from .admin import router as admin_router
from .extract import router as extract_router
from .chunking import router as chunking_router
from .embedding import router as embedding_router
from .query_embedding import router as query_embedding_router
from .search import router as search_router
from .cross_encoder import router as cross_encoder_router
from .generation import router as generation_router
import logging

logger = logging.getLogger(__name__)

app = FastAPI(
    title=__title__,
    description=__description__,
    version=__version__,
)

# CORS 미들웨어
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# JWT 인증 미들웨어
@app.middleware("http")
async def jwt_auth_middleware_handler(request: Request, call_next):
    return await jwt_auth_middleware(request, call_next)

# 라우터 연결 - 공통 prefix /ai/api 추가
app.include_router(admin_router, prefix="/ai/api")
app.include_router(extract_router, prefix="/ai/api")
app.include_router(chunking_router, prefix="/ai/api")
app.include_router(embedding_router, prefix="/ai/api")
app.include_router(query_embedding_router, prefix="/ai/api")
app.include_router(search_router, prefix="/ai/api")
app.include_router(cross_encoder_router, prefix="/ai/api")
app.include_router(generation_router, prefix="/ai/api")

@app.get("/")
async def root():
    return {
        "message": "Hebees API Gateway is running"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": __version__,
    }

@app.get("/ai/api/me")
async def get_current_user(request: Request):
    """현재 사용자 정보 조회"""
    from .common.auth.models import UserInfo
    user = getattr(request.state, 'user', None)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    return {
        "user_uuid": user.user_uuid,
        "role": user.role,
        "is_authenticated": user.is_authenticated
    }