from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.parent


class Settings(BaseSettings):
    app_name: str = "HEBEES Embedding Service"
    host: str = "0.0.0.0"
    port: int = 8000

    # External Embedding Provider
    embedding_provider_url: str = "https://aloojgpo171my1-8000.proxy.runpod.net"

    # Milvus 설정
    milvus_host: str
    milvus_port: int = 19530

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

    # CORS
    allowed_origins: str = "http://localhost:5173,http://localhost:3000"
    @property
    def allowed_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]

    # 로깅 설정
    logging_level: str = "INFO"
    log_file_enabled: bool = False
    log_file_path: str = "/var/log/hebees/embedding.log"
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

