#!/usr/bin/env python3
"""
Ingest Service 실행 스크립트
"""
import os
import uvicorn
from loguru import logger
from app.core.settings import settings

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
DEBUG = os.getenv("DEBUG", "true").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "info")

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
DEBUG = os.getenv("DEBUG", "true").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "info")

if __name__ == "__main__":
    # 기본 로거 설정
    logger.remove()
    logger.add(
        sink=lambda msg: print(msg, end=""),
        level=settings.logging_level.upper(),
        backtrace=True,
        diagnose=False,
    )

    logger.info(f"Starting {settings.app_name}")
    logger.info(f"Server: http://{settings.host}:{settings.port}")
    logger.info(f"Docs: http://{settings.host}:{settings.port}/docs")

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=False,
        log_level=settings.logging_level.lower(),
    )
