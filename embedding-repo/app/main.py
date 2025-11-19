from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from . import __version__, __title__, __description__
from .core.settings import settings
from .routers import router
from datetime import datetime
from .models.database import Base, engine, AsyncSessionLocal
from .core.openapi import custom_openapi
from .service.runpod_service import RunpodService
from loguru import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    애플리케이션 시작/종료 시 실행되는 lifespan 이벤트
    시작 시 DB에서 RUNPOD 정보를 조회하여 embedding_provider_url 업데이트
    """
    # 애플리케이션 시작 시
    logger.info("애플리케이션 시작: RUNPOD 정보 조회 중...")
    try:
        async with AsyncSessionLocal() as db:
            runpod_address = await RunpodService.get_address_by_name(db, "EMBEDDING")
            if runpod_address:
                # settings 객체의 속성 직접 수정
                settings.embedding_provider_url = runpod_address
                logger.info(f"RUNPOD 주소로 embedding_provider_url 업데이트: {runpod_address}")
            else:
                logger.warning(
                    f"DB에서 RUNPOD를 찾을 수 없습니다 (NAME='EMBEDDING'). "
                    f"기본값 사용: {settings.embedding_provider_url}"
                )
    except Exception as e:
        logger.error(
            f"RUNPOD 정보 조회 실패. 기본값 사용: {settings.embedding_provider_url}, "
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

# 데이터베이스 테이블 생성
Base.metadata.create_all(bind=engine)

# Router 등록
app.include_router(router)

@app.get("/")
async def root():
    return {
        "message": "Hebees Embedding Service is running"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": __version__,
    }
