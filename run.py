#!/usr/bin/env python3
"""
Embedding Service 실행 스크립트
"""
import uvicorn

if __name__ == "__main__":
    print("Starting HEBEES Embedding Service")
    print("Server: http://0.0.0.0:8003")
    print("Docs: http://0.0.0.0:8003/docs")
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8003,
        reload=True,
        log_level="info"
    )
