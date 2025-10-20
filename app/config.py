from pydantic_settings import BaseSettings
from typing import List, Optional
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent

class Settings(BaseSettings):
    # 앱 정보
    app_name: str = "HEBEES API Gateway"

    # 서버 정보
    host: str
    port: int

    # CORS 설정
    allowed_origins: str
    
    @property
    def allowed_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",")]

    # RAG DATA PROCESSING PIPELINE URL
    extract_service_url: str
    chunking_service_url: str
    embedding_service_url: str

    # RAG CHAT PIPELINE URL
    query_embedding_service_url: str
    search_service_url: str
    cross_encoder_service_url: str
    generation_service_url: str

    # RunPod 설정
    runpod_api_url: Optional[str] = None
    runpod_api_key: str

    # Milvus 설정
    milvus_host: str
    milvus_port: int

    # Database 설정
    database_url: str
    
    # 로깅
    logging_level: str

    class Config:
        env_file = BASE_DIR / ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

settings = Settings()