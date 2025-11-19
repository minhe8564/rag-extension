#!/usr/bin/env python3
"""
Cross Encoder Service 실행 스크립트
"""
import uvicorn

if __name__ == "__main__":
    print("Starting HEBEES Cross Encoder Service")
    print("Server: http://0.0.0.0:8006")
    print("Docs: http://0.0.0.0:8006/docs")
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8006,
        reload=True,
        log_level="info"
    )
