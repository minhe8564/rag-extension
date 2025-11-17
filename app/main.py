from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from loguru import logger
from . import __version__, __title__, __description__
from .config import settings
from datetime import datetime
from .routers import router
from .core.openapi import custom_openapi
from .models.database import AsyncSessionLocal
from .service.runpod_service import RunpodService


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    애플리케이션 시작/종료 시 실행되는 lifespan 이벤트
    시작 시 DB에서 RUNPOD 정보를 조회하여 marker_provider_url, yolo_provider_url 업데이트
    """
    # 애플리케이션 시작 시
    logger.info("애플리케이션 시작: RUNPOD 정보 조회 중...")
    try:
        async with AsyncSessionLocal() as db:
            # MARKER 주소 조회
            marker_address = await RunpodService.get_address_by_name(db, "MARKER")
            if marker_address:
                settings.marker_provider_url = marker_address
                logger.info(f"RUNPOD 주소로 marker_provider_url 업데이트: {marker_address}")
            else:
                logger.warning(
                    f"DB에서 RUNPOD를 찾을 수 없습니다 (NAME='MARKER'). "
                    f"기본값 사용: {settings.marker_provider_url}"
                )
            
            # YOLO 주소 조회
            yolo_address = await RunpodService.get_address_by_name(db, "YOLO")
            if yolo_address:
                settings.yolo_provider_url = yolo_address
                logger.info(f"RUNPOD 주소로 yolo_provider_url 업데이트: {yolo_address}")
            else:
                logger.warning(
                    f"DB에서 RUNPOD를 찾을 수 없습니다 (NAME='YOLO'). "
                    f"기본값 사용: {settings.yolo_provider_url}"
                )
    except Exception as e:
        logger.error(
            f"RUNPOD 정보 조회 실패. 기본값 사용: "
            f"marker={settings.marker_provider_url}, "
            f"yolo={settings.yolo_provider_url}, "
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
        "message": "Hebees Extract Service is running"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": __version__,
    }
