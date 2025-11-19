"""
파일 관리 서비스
업로드된 파일 저장 및 관리
"""
import uuid
import shutil
import logging
from pathlib import Path
from typing import Optional
from fastapi import UploadFile

from app.core.settings import settings

logger = logging.getLogger(__name__)

class FileService:
    """파일 업로드 및 관리 서비스"""

    def __init__(self):
        self.work_dir = Path(settings.work_dir)
        self.work_dir.mkdir(parents=True, exist_ok=True)

    def save_uploaded_file(self, file: UploadFile) -> Path:
        """
        업로드된 파일을 저장하고 경로 반환
        """
        filename = file.filename or "unknown"
        temp_path = self.work_dir / f"{uuid.uuid4()}_{filename}"

        with open(temp_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        return temp_path

    def get_file_extension(self, file_path: str) -> str:
        """
        파일 확장자 반환
        """
        return Path(file_path).suffix.lower()
    
    def delete_file(self, file_path: Path) -> bool:
        """
        파일 삭제
        """
        try:
            if file_path.exists():
                file_path.unlink()
                return True
        except Exception as e:
            logger.error(f"파일 삭제 실패: {e}", exc_info=True)
            return False