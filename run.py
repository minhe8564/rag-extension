#!/usr/bin/env python3
"""
Query Embedding Service 실행 스크립트
"""
import uvicorn

if __name__ == "__main__":
    print("Starting HEBEES Query Embedding Service")
    print("Server: http://0.0.0.0:8004")
    print("Docs: http://0.0.0.0:8004/docs")
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8004,
        reload=True,
        log_level="info"
    )
