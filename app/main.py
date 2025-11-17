from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from loguru import logger
from . import __version__, __title__, __description__
from .core.settings import settings
from .routers import router
from datetime import datetime
from .core.openapi import custom_openapi
from .core.database import AsyncSessionLocal
from .service.runpod_service import RunpodService


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    애플리케이션 시작/종료 시 실행되는 lifespan 이벤트
    시작 시 DB에서 RUNPOD 정보를 조회하여 qwen_base_url 업데이트
    """
    # 애플리케이션 시작 시
    logger.info("애플리케이션 시작: RUNPOD 정보 조회 중...")
    try:
        async with AsyncSessionLocal() as db:
            # QWEN3 주소 조회
            qwen_address = await RunpodService.get_address_by_name(db, "qwen3")
            if qwen_address:
                settings.qwen_base_url = qwen_address
                logger.info(f"RUNPOD 주소로 qwen_base_url 업데이트: {qwen_address}")
            else:
                logger.warning(
                    f"DB에서 RUNPOD를 찾을 수 없습니다 (NAME='qwen3'). "
                    f"기본값 사용: {settings.qwen_base_url}"
                )
    except Exception as e:
        logger.error(
            f"RUNPOD 정보 조회 실패. 기본값 사용: {settings.qwen_base_url}, "
            f"오류: {e}",
            exc_info=True
        )
    
    yield
    
    # 애플리케이션 종료 시 (필요한 경우 정리 작업 수행)
    logger.info("애플리케이션 종료")


app = FastAPI(
    title=__title__,
    description=__description__,
    version=__version__,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.openapi = lambda: custom_openapi(app)

# Router 등록
app.include_router(router)

@app.get("/")
async def root():
    return {
        "message": "Hebees Generation Service is running"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": __version__,
    }
