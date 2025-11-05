from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from . import __version__, __title__, __description__
from .core.settings import settings
from .core.utils import custom_openapi

from .domains.file.routers.file_category import router as file_router
from .domains.image.routers.image_controller import router as image_router
from .domains.rag_setting.routers.strategy_router import router as strategy_router
from .domains.rag_setting.routers.ingest_router import router as ingest_router
from .domains.monitoring.routers.monitoring_controller import router as monitoring_router
from datetime import datetime

app = FastAPI(
    title=__title__,
    description=__description__,
    version=__version__,
    swagger_ui_parameters={
        "persistAuthorization": True,
    },
)

app.openapi_schema = None
app.openapi = lambda: custom_openapi(app)

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

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(file_router, prefix="/api/v1")
app.include_router(image_router, prefix="/api/v1")
app.include_router(strategy_router, prefix="/api/v1")
app.include_router(ingest_router, prefix="/api/v1")
app.include_router(monitoring_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {
        "message": "Hebees Python Backend Service is running",
        "app_name": settings.app_name,
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": __version__,
        "timestamp": datetime.now().isoformat(),
    }
