from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from app.core.settings import settings
from app.routers import marker_controller
from app.processors import ProcessorFactory

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    애플리케이션 시작/종료 시 실행되는 이벤트 핸들러
    - 시작 시: PDFProcessor의 Marker 모델을 미리 로드
    - 종료 시: 정리 작업 (필요시)
    """
    # 시작 시: Marker 모델 미리 로드
    logger.info("애플리케이션 시작: Marker 모델 로딩 중...")
    try:
        # PDFProcessor 인스턴스를 가져와서 모델을 미리 로드
        from app.processors.pdf_processor import PDFProcessor
        
        pdf_processor = None
        for processor in ProcessorFactory._processors:
            if isinstance(processor, PDFProcessor):
                pdf_processor = processor
                break
        
        if pdf_processor:
            # 모델을 미리 로드 (동기 작업이므로 별도 스레드에서 실행)
            import asyncio
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, pdf_processor._ensure_model)
            logger.info("Marker 모델 로딩 완료")
        else:
            logger.warning("PDFProcessor를 찾을 수 없습니다.")
    except Exception as e:
        logger.error(f"Marker 모델 로딩 실패: {e}", exc_info=True)
        # 모델 로딩 실패해도 애플리케이션은 시작 (lazy loading으로 fallback)
    
    yield
    
    # 종료 시: 정리 작업 (필요시)
    logger.info("애플리케이션 종료")


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan
)


# 커스텀 Exception Handler
@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    """
    HTTPException을 프로젝트 표준 응답 형식으로 변환
    
    모든 HTTPException을 BaseResponse 형식으로 통일:
    - status: HTTP 상태 코드
    - code: 에러 코드 (VALIDATION_FAILED, FORBIDDEN 등)
    - message: 에러 메시지
    - isSuccess: False (항상)
    - result: 추가 정보 (빈 객체 또는 상세 정보)
    """
    # HTTP 상태 코드별 에러 코드 매핑
    error_codes = {
        400: "VALIDATION_FAILED",
        401: "INVALID_ACCESS_TOKEN",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        409: "CONFLICT",
        500: "INTERNAL_SERVER_ERROR",
    }

    # detail이 딕셔너리인 경우 (추가 정보 포함)
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
app.include_router(marker_controller.router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"message": "Hello from RAG Data Marker!"}


@app.get("/health")
async def health():
    return {"status": "healthy"}