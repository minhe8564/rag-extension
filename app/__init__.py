import logging
import os
from logging.handlers import RotatingFileHandler
from .config import settings

"""
Hebees FastAPI Gateway
"""
__version__ = "0.0.1"
__author__ = "RAG EXTENSION"
__title__ = "HEBEES API Gateway"
__description__ = "HEBEES FastAPI Gateway"


# 로깅 설정
logging.basicConfig(
    level=getattr(logging, settings.logging_level.upper(), logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

if settings.log_file_enabled:
    try:
        log_path = settings.log_file_path
        log_dir = os.path.dirname(log_path) or "."
        os.makedirs(log_dir, exist_ok=True)

        root_logger = logging.getLogger()
        exists = False
        for h in root_logger.handlers:
            if isinstance(h, RotatingFileHandler):
                try:
                    if os.path.abspath(getattr(h, 'baseFilename', '')) == os.path.abspath(log_path):
                        exists = True
                        break
                except Exception:
                    pass
        if not exists:
            file_handler = RotatingFileHandler(
                filename=log_path,
                maxBytes=settings.log_file_max_bytes,
                backupCount=settings.log_file_backup_count,
                encoding="utf-8"
            )
            file_handler.setLevel(getattr(logging, settings.logging_level.upper(), logging.INFO))
            file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            root_logger.addHandler(file_handler)
    except Exception as e:
        logging.getLogger(__name__).warning(f"파일 로깅 설정 중 오류: {e}")
