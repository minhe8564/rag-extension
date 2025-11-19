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

    # JWT 설정 (개선된 버전)
    jwt_secret: str = "hebees-secret-key-for-jwt-token-generation-and-validation-256-bits"
    jwt_algorithm: str = "HS512"
    jwt_supported_algorithms: List[str] = ["HS256", "HS512"]
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    # EXTRACT SERVICE URL
    extract_service_url: str
    chunking_service_url: str
    embedding_service_url: str
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
    logging_level: str = "INFO"

    class Config:
        env_file = BASE_DIR / ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"

settings = Settings()