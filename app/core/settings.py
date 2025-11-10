from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.parent


class Settings(BaseSettings):
    app_name: str = "HEBEES Ingest Service"
    host: str = "0.0.0.0"
    port: int = 8000
    # CORS
    allowed_origins: str = "http://localhost:5173,http://localhost:3000"
    @property
    def allowed_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",")]

    # Milvus 설정
    milvus_host: str
    milvus_port: int = 19530

    # Gateway 설정
    gateway_url: str

    # Database 설정
    db_host: str
    db_port: int = 3306
    db_username: str
    db_password: str

    @property
    def database_url(self) -> str:
        return f"mysql+aiomysql://{self.db_username}:{self.db_password}@{self.db_host}:{self.db_port}/hebees-test"

    # Redis 설정
    redis_host: str
    redis_port: int = 16379
    redis_username: Optional[str] = None
    redis_password: Optional[str] = None
    redis_db: int = 1

    # Gateway 및 내부 서비스 URL (서비스 간 직접 통신용)
    gateway_url: str = "http://rag-extension-gw:8000"
    extract_service_url: str = "http://hebees-extract:8000"
    chunking_service_url: str = "http://hebees-chunking:8000"
    embedding_service_url: str = "http://hebees-embedding:8000"
    query_embedding_service_url: str = "http://hebees-query-embedding:8000"
    search_service_url: str = "http://hebees-search:8000"
    cross_encoder_service_url: str = "http://hebees-cross-encoder:8000"
    generation_service_url: str = "http://hebees-generation:8000"

    # 로깅 설정
    logging_level: str = "INFO"
    log_file_enabled: bool = False
    log_file_path: str = "/var/log/hebees/ingest.log"
    log_file_max_bytes: int = 10_485_760  # 10MB
    log_file_backup_count: int = 5

    # Environment
    environment: str = "production"
    debug: bool = False

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @classmethod
    def settings_customise_sources(
        cls, settings_cls, init_settings, env_settings, dotenv_settings, file_secret_settings
    ):
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            file_secret_settings,
        )


settings = Settings()

