from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.parent


class Settings(BaseSettings):
    app_name: str = "HEBEES Generation Service"
    host: str = "0.0.0.0"
    port: int = 8000

    # CORS
    allowed_origins: str = "http://localhost:5173,http://localhost:3000"

    @property
    def allowed_origins_list(self) -> list[str]:
        try:
            return [origin.strip() for origin in (self.allowed_origins or "").split(",") if origin.strip()]
        except Exception:
            return ["*"]

    # OpenAI 설정
    openai_api_key: str

    # MongoDB 설정
    mongo_host: str
    mongo_port: int = 27017
    mongo_username: str
    mongo_password: str
    mongo_database: str

    @property
    def mongo_url(self) -> str:
        return f"mongodb://{self.mongo_username}:{self.mongo_password}@{self.mongo_host}:{self.mongo_port}/{self.mongo_database}"

    # Redis 설정
    redis_host: str
    redis_port: int = 16379
    redis_username: Optional[str] = None
    redis_password: Optional[str] = None
    redis_db: int = 1

    # 로깅 설정
    logging_level: str = "INFO"
    log_file_enabled: bool = False
    log_file_path: str = "/var/log/hebees/generation.log"
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

