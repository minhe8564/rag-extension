#!/usr/bin/env python3
"""
Extract Service 실행 스크립트
"""
import uvicorn

if __name__ == "__main__":
    print("Starting HEBEES Extract Service")
    print("Server: http://0.0.0.0:8001")
    print("Docs: http://0.0.0.0:8001/docs")
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )
