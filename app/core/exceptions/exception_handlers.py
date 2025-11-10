from __future__ import annotations

from typing import Any, Dict

from fastapi import HTTPException, Request, FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


def _base_error_response(
    status_code: int,
    code: str,
    message: str,
    result: Dict[str, Any] | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "status": status_code,
            "code": code,
            "message": message,
            "isSuccess": False,
            "result": result or {},
        },
    )


def _http_error_code(status_code: int) -> str:
    mapping = {
        400: "BAD_REQUEST",
        401: "INVALID_ACCESS_TOKEN",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        409: "CONFLICT",
        422: "VALIDATION_FAILED",
        500: "INTERNAL_SERVER_ERROR",
    }
    return mapping.get(status_code, "HTTP_EXCEPTION")


async def http_exception_handler(request: Request, exc: HTTPException):
    if isinstance(exc.detail, dict):
        message = exc.detail.get("message", "요청 처리 중 오류가 발생했습니다.")
        result = {k: v for k, v in exc.detail.items() if k != "message"}
    else:
        message = str(exc.detail)
        result = {}

    return _base_error_response(
        exc.status_code,
        _http_error_code(exc.status_code),
        message,
        result,
    )


async def starlette_http_exception_handler(request: Request, exc: StarletteHTTPException):
    message = exc.detail if isinstance(exc.detail, str) else "HTTP Error"
    return _base_error_response(
        exc.status_code,
        _http_error_code(exc.status_code),
        message,
        {},
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    try:
        for e in exc.errors():
            loc = ".".join([str(x) for x in e.get("loc", [])])
            msg = e.get("msg", "Invalid input")
            errors.append({"field": loc, "message": msg})
    except Exception:
        pass

    return _base_error_response(
        422,
        "VALIDATION_FAILED",
        "요청 유효성 검증에 실패했습니다.",
        {"errors": errors} if errors else {},
    )


async def unhandled_exception_handler(request: Request, exc: Exception):
    return _base_error_response(
        500,
        "INTERNAL_SERVER_ERROR",
        "서버 내부 오류가 발생했습니다.",
        {},
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(StarletteHTTPException, starlette_http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

