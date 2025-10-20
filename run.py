#!/usr/bin/env python3
"""
Search Service 실행 스크립트
"""
import uvicorn

if __name__ == "__main__":
    print("Starting HEBEES Search Service")
    print("Server: http://0.0.0.0:8005")
    print("Docs: http://0.0.0.0:8005/docs")
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8005,
        reload=True,
        log_level="info"
    )
