from pydantic_settings import BaseSettings
from typing import List, Optional
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent

class Settings(BaseSettings):
    app_name: str = "HEBEES API Gateway"
    host: str = "0.0.0.0"
    port: int = 8000
    allowed_origins: str = "http://localhost:5173,http://localhost:3000"
    
    @property
    def allowed_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",")]

    # EXTRACT SERVICE URL
    extract_service_url: str
    chunking_service_url: str
    embedding_service_url: str

    # RunPod 설정
    runpod_api_url: Optional[str] = None
    runpod_api_key: str

    # Milvus 설정
    milvus_host: str
    milvus_port: int

    # Database 설정
    database_url: str

    # 로깅
    logging_level: str = "INFO"

    class Config:
        env_file = BASE_DIR / ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # 추가 필드 무시

settings = Settings()
