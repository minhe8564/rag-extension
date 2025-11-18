from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
from pathlib import Path
import re

# Project root (two levels above 'app/core')
BASE_DIR = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    app_name: str = "HEBEES Python Backend Service"
    host: str = "0.0.0.0"
    port: int = 8000

    # CORS
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

    # Database
    db_host: str
    db_port: int
    db_name: str
    db_username: str
    db_password: str

    @property
    def database_url(self) -> str:
        return f"mysql+aiomysql://{self.db_username}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    # MinIO 설정
    minio_endpoint: str = ""
    minio_access_key: str = ""
    minio_secret_key: str = ""
    minio_image_bucket_name: str = ""
    minio_use_ssl: bool = False
    minio_region: str = ""
    minio_api_public_url: str = ""
    minio_use_presigned_url: bool = False

    # Gemini API 설정
    gemini_api_key: str = ""
    gemini_image_model_name: str = ""

    # LLM 설정 (매출 리포트 AI 요약용)
    llm_provider: str = "gpt"  # "qwen" or "gpt"
    openai_api_key: str = ""  # GPT 사용 시 필요 (환경 변수 OPENAI_API_KEY에서 자동 로드)
    openai_model: str = "gpt-4o-mini"  # GPT 모델명 (환경 변수 OPENAI_MODEL에서 자동 로드)

    # Monitoring 설정
    network_bandwidth_mbps: float = 1000.0  # 네트워크 총 대역폭(Mbps), 기본값 1Gbps

    @property
    def minio_endpoint_url(self) -> str:
        """MinIO 엔드포인트 URL"""
        protocol = "https" if self.minio_use_ssl else "http"
        return f"{protocol}://{self.minio_endpoint}"
    
    @property
    def minio_public_endpoint_url(self) -> str:
        """MinIO API 공개 접근 URL"""
        if self.minio_api_public_url:
            return self.minio_api_public_url.rstrip("/")
        return self.minio_endpoint_url

    # External APIs
    ingest_base_url: str = "http://hebees-rag-orchestrator:8000"
    ingest_process_url: str = ""  # 환경 변수로 직접 설정 가능
    ingest_delete_url: str = ""  # optional: vector cleanup endpoint

    @property
    def ingest_process_url_resolved(self) -> str:
        """ingest_process_url이 설정되어 있으면 사용, 없으면 ingest_base_url 기반으로 생성"""
        if self.ingest_process_url:
            return self.ingest_process_url
        return f"{self.ingest_base_url}/ingest/process"

    # Redis
    redis_url: str = "redis://localhost:6379/1"
    redis_db: int = 1
    redis_metrics_db: int = 8
    ingest_meta_ttl_sec: int = 0  # 0 or less disables TTL

    # Milvus settings (direct access)
    milvus_host: str = ""
    milvus_port: int
    milvus_collection: str = ""  # e.g., "documents" or "chunks"
    milvus_pk_field: str = "file_no"  # field name storing file UUID as string
    milvus_path_field: str = "path"  # optional secondary field to match by path

    # Logging
    logging_level: str = "INFO"
    log_file_enabled: bool = False
    log_file_path: str = "/var/log/hebees/python-backend.log"
    log_file_max_bytes: int = 10_485_760  # 10MB
    log_file_backup_count: int = 5

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @classmethod
    def settings_customise_sources(cls, settings_cls, init_settings, env_settings, dotenv_settings, file_secret_settings):
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            file_secret_settings,
        )


settings = Settings()
