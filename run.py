#!/usr/bin/env python3
"""
Cross Encoder Service 실행 스크립트
"""
import os
import uvicorn
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv(".env", override=False)

# 환경변수에서 설정값 가져오기
HOST = os.getenv("HOST")
PORT = int(os.getenv("PORT"))
DEBUG = os.getenv("DEBUG").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL")
ENVIRONMENT = os.getenv("ENVIRONMENT")

if __name__ == "__main__":
    print("Starting HEBEES Cross Encoder Service")
    print(f"Environment: {ENVIRONMENT}")
    print(f"Debug: {DEBUG}")
    print(f"Server: http://{HOST}:{PORT}")
    print(f"Docs: http://{HOST}:{PORT}/docs")
    
    uvicorn.run(
        "app.main:app",
        host=HOST,
        port=PORT,
        reload=DEBUG,
        log_level=LOG_LEVEL
    )
