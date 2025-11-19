from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
from pathlib import Path
import re

BASE_DIR = Path(__file__).parent.parent.parent

class Settings(BaseSettings):
    app_name: str = "HEBEES FastAPI Gateway"
    host: str = "0.0.0.0"
    port: int = 8000

    # CORS 설정
    allowed_origins: str = "http://localhost:5173,http://localhost:3000"

    @property
    def allowed_origins_list(self) -> List[str]:
        """일반 도메인만 반환 (와일드카드 제외)"""
        origins = []
        for origin in self.allowed_origins.split(","):
            origin = origin.strip()
            # 와일드카드 패턴이 아닌 경우만 추가
            if origin and "*" not in origin:
                origins.append(origin)
        return origins

    @property
    def allowed_origin_regex_list(self) -> List[str]:
        """와일드카드 패턴을 정규식으로 변환하여 반환"""
        regex_patterns = []
        for origin in self.allowed_origins.split(","):
            origin = origin.strip()
            if not origin:
                continue
            
            # 와일드카드 패턴 감지 (*.domain.com 형식)
            if origin.startswith("*."):
                # *.beta9.kr -> https?://.*\.beta9\.kr
                domain = origin[2:]  # *. 제거
                # 프로토콜이 없는 경우 http/https 모두 지원
                regex = f"https?://.*\\.{re.escape(domain)}"
                regex_patterns.append(regex)
            elif "*" in origin:
                # 다른 와일드카드 패턴 처리 (예: https://*.beta9.kr)
                # 프로토콜이 있는 경우
                if origin.startswith("http://*."):
                    domain = origin[8:]  # http://*. 제거
                    regex = f"http://.*\\.{re.escape(domain)}"
                    regex_patterns.append(regex)
                elif origin.startswith("https://*."):
                    domain = origin[9:]  # https://*. 제거
                    regex = f"https://.*\\.{re.escape(domain)}"
                    regex_patterns.append(regex)
        
        return regex_patterns

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

