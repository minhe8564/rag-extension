from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import Optional
import json


class Settings(BaseSettings):
    """애플리케이션 설정 클래스"""
    
    # API 설정
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "RAG Data YOLO"
    VERSION: str = "1.0.0"
    
    # 서버 설정
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False
    
    # CORS 설정 (JSON 문자열 또는 쉼표로 구분된 문자열)
    CORS_ORIGINS: str = '["*"]'
    
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
                return json.loads(v)
            except json.JSONDecodeError:
                # 쉼표로 구분된 문자열인 경우
                return [origin.strip() for origin in v.split(",") if origin.strip()]
        return ["*"]
    
    @property
    def cors_origins_list(self) -> list[str]:
        """CORS_ORIGINS를 리스트로 반환"""
        if isinstance(self.CORS_ORIGINS, list):
            return self.CORS_ORIGINS
        return self.parse_cors_origins(self.CORS_ORIGINS)
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
