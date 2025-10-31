"""
HEBEES FastAPI Gateway
"""
import logging
import os
from logging.handlers import RotatingFileHandler
from .core.settings import settings

__version__ = "0.0.1"
__author__ = "RAG EXTENSION"
__title__ = "HEBEES API Gateway"
__description__ = "HEBEES FastAPI Gateway - RAG Orchestrator Proxy"


# 로깅 설정
logging.basicConfig(
    level=getattr(logging, settings.logging_level.upper(), logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

if settings.log_file_enabled:
    try:
        log_file_path = settings.log_file_path
        log_directory = os.path.dirname(log_file_path) or "."
        os.makedirs(log_directory, exist_ok=True)

        root_logger = logging.getLogger()
        file_handler_exists = False
        
        # 기존 파일 핸들러 중복 확인
        for existing_handler in root_logger.handlers:
            if isinstance(existing_handler, RotatingFileHandler):
                try:
                    existing_handler_path = os.path.abspath(getattr(existing_handler, 'baseFilename', ''))
                    if existing_handler_path == os.path.abspath(log_file_path):
                        file_handler_exists = True
                        break
                except Exception:
                    pass
        
        # 파일 핸들러가 없으면 생성
        if not file_handler_exists:
            file_handler = RotatingFileHandler(
                filename=log_file_path,
                maxBytes=settings.log_file_max_bytes,
                backupCount=settings.log_file_backup_count,
                encoding="utf-8"
            )
            file_handler.setLevel(getattr(logging, settings.logging_level.upper(), logging.INFO))
            file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            root_logger.addHandler(file_handler)
    except Exception as error:
        logging.getLogger(__name__).warning(f"파일 로깅 설정 중 오류: {error}")