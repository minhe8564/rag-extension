#!/usr/bin/env python3
"""
Search Service 실행 스크립트
"""
import os
import uvicorn
from app.core.settings import settings

if __name__ == "__main__":
    print(f"Starting {settings.app_name}")
    print(f"Server: http://{settings.host}:{settings.port}")
    print(f"Docs: http://{settings.host}:{settings.port}/docs")
    
    # uvicorn 서버 설정
    config = uvicorn.Config(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=False,
        log_level=settings.logging_level.lower(),
        timeout_keep_alive=600,  # 10분
        timeout_graceful_shutdown=600,
        limit_concurrency=100,  # 동시 연결 수 제한
        limit_max_requests=1000,  # 최대 요청 수
    )
    server = uvicorn.Server(config)
    server.run()