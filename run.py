#!/usr/bin/env python3
"""
Chunking Service 실행 스크립트
"""
import uvicorn

if __name__ == "__main__":
    print("Starting HEBEES Chunking Service")
    print("Server: http://0.0.0.0:8002")
    print("Docs: http://0.0.0.0:8002/docs")
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8002,
        reload=True,
        log_level="info"
    )
