"""
FILE 테이블 모델
이미지 파일 메타데이터를 저장하는 모델
"""

from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, CHAR, BINARY
from sqlalchemy.dialects.mysql import BINARY as MySQL_BINARY, CHAR as MySQL_CHAR
from datetime import datetime
import uuid
from app.core.database.base import Base

class File(Base):
    """
    FILE 테이블 모델
    MinIO에 저장된 이미지 파일의 메타데이터 관리
    """
    __tablename__ = "FILE"
    
    # Primary Key
    file_no = Column(
        "FILE_NO",
        MySQL_BINARY(16),
        primary_key=True
    )
    
    # User Foreign Key
    user_no = Column(
        "USER_NO",
        MySQL_BINARY(16),
        ForeignKey("USER.USER_NO"),
        nullable=False,
        index=True
    )
    
    # File Information
    name = Column("NAME", String(255), nullable=False)
    size = Column("SIZE", Integer, nullable=False)
    type = Column("TYPE", String(50), nullable=False)
    hash = Column("HASH", String(64), nullable=True)
    description = Column("DESCRIPTION", Text, nullable=True)
    
    # Storage Information
    bucket = Column("BUCKET", String(255), nullable=False)
    path = Column("PATH", String(500), nullable=False)
    status = Column("STATUS", String(20), nullable=False, default="PENDING", server_default="PENDING", index=True)
    
    # Foreign Keys
    file_category_no = Column(
        "FILE_CATEGORY_NO",
        MySQL_BINARY(16),
        ForeignKey("FILE_CATEGORY.FILE_CATEGORY_NO"),
        nullable=False,
        index=True
    )
    
    offer_no = Column(
        "OFFER_NO",
        MySQL_CHAR(10),
        ForeignKey("OFFER.OFFER_NO"),
        nullable=False,
        index=True
    )
    
    collection_no = Column(
        "COLLECTION_NO",
        MySQL_BINARY(16),
        nullable=True
    )
    
    source_no = Column(
        "SOURCE_NO",
        MySQL_BINARY(16),
        nullable=True
    )
    
    # Timestamps
    created_at = Column("CREATED_AT", DateTime, nullable=False)
    updated_at = Column("UPDATED_AT", DateTime, nullable=False)
    
    def __repr__(self):
        return f"<File(file_no={self.file_no.hex() if self.file_no else None}, name={self.name}, path={self.path})>"

