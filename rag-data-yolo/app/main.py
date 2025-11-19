from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.settings import settings
from app.routers import yolo_controller

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    애플리케이션 시작/종료 시 실행되는 이벤트 핸들러
    - 시작 시: YOLO 모델을 미리 로드
    - 종료 시: 정리 작업 (필요시)
    """
    # 시작 시: YOLO 모델 미리 로드
    logger.info("애플리케이션 시작: YOLO 모델 로딩 중...")
    try:
        from app.processors.yolo_processor import YOLOProcessor
        processor = YOLOProcessor()
        # 모델을 미리 로드 (동기 작업이므로 별도 스레드에서 실행)
        import asyncio
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            processor._ensure_model,
            settings.YOLO_WEIGHTS
        )
        logger.info("YOLO 모델 로딩 완료")
    except Exception as e:
        logger.error(f"YOLO 모델 로딩 실패: {e}", exc_info=True)
        # 모델 로딩 실패해도 애플리케이션은 시작 (lazy loading으로 fallback)
    
    yield
    
    # 종료 시: 정리 작업 (필요시)
    logger.info("애플리케이션 종료")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 커스텀 Exception Handler
@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    """HTTPException을 프로젝트 표준 응답 형식으로 변환"""
    error_codes = {
        400: "VALIDATION_FAILED",
        401: "INVALID_ACCESS_TOKEN",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        409: "CONFLICT",
        500: "INTERNAL_SERVER_ERROR",
    }
    
    if isinstance(exc.detail, dict):
        message = exc.detail.get("message", "요청 처리 중 오류가 발생했습니다.")
        result = {k: v for k, v in exc.detail.items() if k != "message"}
    else:
        message = exc.detail
        result = {}
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": exc.status_code,
            "code": error_codes.get(exc.status_code, "UNKNOWN_ERROR"),
            "message": message,
            "isSuccess": False,
            "result": result
        }
    )

# 라우터 등록
app.include_router(yolo_controller.router, prefix=settings.API_V1_STR)

@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": f"Welcome to {settings.PROJECT_NAME}",
        "version": settings.VERSION,
    }

@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )

