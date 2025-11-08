from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
from pathlib import Path

# Project root (two levels above 'app/core')
BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_name: str = "HEBEES Python Backend Service"
    host: str = "0.0.0.0"
    port: int = 8000

    # CORS
    allowed_origins: str = "http://localhost:5173,http://localhost:3000"

    @property
    def allowed_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",")]

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
    minio_image_storage_base_path: str = ""

    # Gemini API 설정
    gemini_api_key: str = ""
    gemini_image_model_name: str = ""

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
    ingest_process_url: str = "https://gateway.ragextension.shop/rag/ingest/process"
    ingest_delete_url: str = ""  # optional: vector cleanup endpoint

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
