from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "RAG Data Marker"
    host: str = "0.0.0.0"
    port: int = 8000
    logging_level: str = "INFO"
    
    # Marker 설정
    # .env 파일에서 읽어오고, 없으면 기본값은 "auto" (자동 선택: CUDA > MPS > CPU)
    # "cuda", "mps", "cpu"로 명시적으로 지정 가능
    marker_device: str = "auto"
    marker_dtype: str = "float16"
    work_dir: str = "./work"
    
    # Hugging Face 캐시 경로
    hf_home: str = "./cache/hf"
    transformers_cache: str = "./cache/hf"

    # MinIO 설정
    minio_endpoint: str
    minio_access_key: str
    minio_secret_key: str
    minio_bucket_name: str
    minio_secure: bool = False  # HTTP 사용 (False) 또는 HTTPS 사용 (True)
    minio_base_url: str = "https://storage.ragextension.shop"  # MinIO 공개 URL

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="",  # 환경 변수명에 prefix 없이 사용
        case_sensitive=False,  # 대소문자 구분 안 함
    )


settings = Settings()