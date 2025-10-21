#!/usr/bin/env python3
"""
Generation Service 실행 스크립트
"""
import uvicorn

if __name__ == "__main__":
    print("Starting HEBEES Generation Service")
    print("Server: http://0.0.0.0:8007")
    print("Docs: http://0.0.0.0:8007/docs")
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8007,
        reload=True,
        log_level="info"
    )
