#!/usr/bin/env python3
"""
Extract Service 실행 스크립트
"""
import os
import uvicorn
from app.core.settings import settings

if __name__ == "__main__":
    print(f"Starting {settings.app_name}")
    print(f"Server: http://{settings.host}:{settings.port}")
    print(f"Docs: http://{settings.host}:{settings.port}/docs")

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=False,
        log_level=settings.logging_level.lower(),
    )