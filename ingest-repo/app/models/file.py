from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.dialects.mysql import BINARY
from sqlalchemy.sql import func
from app.core.database import Base


class File(Base):
    __tablename__ = "FILE"

    # 기본 키 및 참조 키 (UUID BINARY(16) 형식)
    file_no = Column("FILE_NO", BINARY(16), primary_key=True, nullable=False)
    user_no = Column("USER_NO", BINARY(16), nullable=False)

    # 파일 메타데이터
    name = Column("NAME", String(255), nullable=False)
    size = Column("SIZE", Integer, nullable=False)  # bytes 단위
    type = Column("TYPE", String(20), nullable=False)  # 예: pdf, png, xlsx
    hash = Column("HASH", String(255), nullable=False)
    description = Column("DESCRIPTION", Text, nullable=False, default="")

    # 저장 위치 (MinIO 등)
    bucket = Column("BUCKET", String(255), nullable=False)
    path = Column("PATH", String(255), nullable=False)
    status = Column("STATUS", String(20), nullable=False, default="PENDING")

    # 분류 및 연계 정보
    file_category_no = Column("FILE_CATEGORY_NO", BINARY(16), nullable=False)
    offer_no = Column("OFFER_NO", String(10), nullable=False)  # 사업자 번호
    source_no = Column("SOURCE_NO", BINARY(16), nullable=True)  # 소스 파일은 NULL 가능
    collection_no = Column("COLLECTION_NO", BINARY(16), nullable=False)

    # 생성/수정 시각
    created_at = Column("CREATED_AT", DateTime, nullable=False, server_default=func.now())
    updated_at = Column("UPDATED_AT", DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    @property
    def file_extension(self) -> str:
        """파일 유형(type)을 소문자로 반환 (확장자 표준화)."""
        return (self.type or "").lower()

    def __repr__(self) -> str: # Java의 toString() 메서드와 같은 역할
        return f"<File name={self.name} type={self.type} size={self.size} bucket={self.bucket} path={self.path}>"

