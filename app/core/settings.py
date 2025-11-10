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
    milvus_host: str = "milvus-standalone"
    milvus_port: int = 19530

    # Gateway 설정
    # (게이트웨이 컨테이너 서비스명과 포트 기준)
    # 실제 런타임에서는 환경변수로 재정의 가능
    # docker-compose: GATEWAY_URL=http://fastapi-gateway:8000
    # 아래 기본값으로 설정
    # 중복 정의 방지를 위해 gateway_url은 아래 '서비스 URL' 섹션의 기본값을 사용합니다.

    # Database 설정
    db_host: str = "database-mysql"
    db_port: int = 3306
    db_username: str = "s407test"
    db_password: str = "q1w2e3r4"

    @property
    def database_url(self) -> str:
        return f"mysql+aiomysql://{self.db_username}:{self.db_password}@{self.db_host}:{self.db_port}/hebees-test"

    # Redis 설정
    redis_host: str = "database-redis"
    redis_port: int = 6379
    redis_username: Optional[str] = None
    redis_password: Optional[str] = "1q2w3e4r"
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

