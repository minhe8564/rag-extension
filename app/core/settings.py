from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.parent

class Settings(BaseSettings):
    app_name: str = "HEBEES FastAPI Gateway"
    host: str = "0.0.0.0"
    port: int = 8000

    # CORS 설정
    allowed_origins: str = "http://localhost:5173,http://localhost:3000"

    @property
    def allowed_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",")]

    # JWT 설정
    jwt_secret: str
    jwt_algorithm: str = "HS512"
    jwt_supported_algorithms: List[str] = ["HS256", "HS512"]
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    # RAG Orchestrator 설정
    rag_orchestrator_url: str

    # Python Backend 설정
    python_backend_url: str

    # Database 설정 (JWT 인증, 사용자 관리, RUNPOD 주소 관리)
    db_host: str
    db_port: int
    db_name: str
    db_username: str
    db_password: str

    @property
    def database_url(self) -> str:
        return f"mysql+aiomysql://{self.db_username}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    # 로깅 설정
    logging_level: str = "INFO"
    log_file_enabled: bool = False
    log_file_path: str = "/var/log/hebees/fastapi-gateway.log"
    log_file_max_bytes: int = 10_485_760 # 10MB
    log_file_backup_count: int = 5

    model_config = SettingsConfigDict(
        env_file = BASE_DIR / ".env",
        env_file_encoding = "utf-8",
        case_sensitive = False,
        extra = "ignore",
    )

    @classmethod
    def settings_customise_sources(
        cls, 
        settings_cls, 
        init_settings, 
        env_settings, 
        dotenv_settings, 
        file_secret_settings
    ):
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            file_secret_settings
        )

settings = Settings()

