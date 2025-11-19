from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import Optional, Union
import json


class Settings(BaseSettings):
    """애플리케이션 설정 클래스"""
    
    # API 설정
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "RAG Data YOLO"
    VERSION: str = "1.0.0"
    
    # 서버 설정
    HOST: str = "0.0.0.0"
    PORT: int = 7002
    WORKERS: int = 1
    DEBUG: bool = False
    
    # YOLO 설정
    # .env 파일에서 환경 변수로 설정 가능:
    #   YOLO_DEVICE=auto    # "auto" (자동 선택: CUDA > MPS > CPU), "cuda", "mps", "cpu"
    #   YOLO_WEIGHTS=./weights/doclayout_yolo_docstructbench_imgsz1024.pt  # 모델 가중치 경로
    #   YOLO_CONF=0.4       # confidence 임계값
    #   WORK_DIR=./work     # 작업 디렉토리 경로
    YOLO_DEVICE: str = "auto"
    YOLO_WEIGHTS: str = "./weights/doclayout_yolo_docstructbench_imgsz1024.pt"
    YOLO_CONF: float = 0.4
    WORK_DIR: str = "./work"
    
    # CORS 설정 (JSON 문자열, 쉼표로 구분된 문자열, 또는 리스트)
    CORS_ORIGINS: Union[str, list[str]] = '["*"]'
    
    # 데이터베이스 설정 (필요시 사용)
    DATABASE_URL: Optional[str] = None
    
    # 기타 설정
    SECRET_KEY: Optional[str] = None
    
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """CORS_ORIGINS를 리스트로 변환"""
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            try:
                # JSON 문자열인 경우
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
                return [parsed]
            except json.JSONDecodeError:
                # 쉼표로 구분된 문자열인 경우
                return [origin.strip() for origin in v.split(",") if origin.strip()]
        return ["*"]
    
    @property
    def cors_origins_list(self) -> list[str]:
        """CORS_ORIGINS를 리스트로 반환"""
        if isinstance(self.CORS_ORIGINS, list):
            return self.CORS_ORIGINS
        if isinstance(self.CORS_ORIGINS, str):
            try:
                parsed = json.loads(self.CORS_ORIGINS)
                if isinstance(parsed, list):
                    return parsed
                return [parsed]
            except json.JSONDecodeError:
                return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]
        return ["*"]
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
