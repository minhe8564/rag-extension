from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.parent


class Settings(BaseSettings):
    app_name: str = "HEBEES Query Embedding Service"
    host: str = "0.0.0.0"
    port: int = 8000

    # 로깅 설정
    logging_level: str = "INFO"
    log_file_enabled: bool = False
    log_file_path: str = "/var/log/hebees/query-embedding.log"
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






