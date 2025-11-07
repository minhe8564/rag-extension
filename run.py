#!/usr/bin/env python3
"""
YOLO Service
"""
import os
import uvicorn
from app.core.settings import settings

if __name__ == "__main__":
    print(f"Starting {settings.PROJECT_NAME}")
    print(f"Server: http://{settings.HOST}:{settings.PORT}")
    print(f"Docs: http://{settings.HOST}:{settings.PORT}/docs")
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        workers=getattr(settings, 'WORKERS', 1),
        reload=settings.DEBUG,
        log_level=getattr(settings, 'LOGGING_LEVEL', 'INFO').lower(),
    )

