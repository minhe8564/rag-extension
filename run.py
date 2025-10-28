#!/usr/bin/env python3
"""
Query Service 실행 스크립트
"""
import uvicorn

if __name__ == "__main__":
    print("Starting HEBEES Query Service")
    print("Server: http://0.0.0.0:8008")
    print("Docs: http://0.0.0.0:8008/docs")
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8008,
        reload=True,
        log_level="info"
    )
