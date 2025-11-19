"""
RUNPOD 테이블 모델
Runpod 이름 및 주소를 저장하는 모델
"""

from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.mysql import BINARY as MySQL_BINARY
from datetime import datetime
from app.core.database import Base


class Runpod(Base):
    """
    RUNPOD 테이블 모델
    Runpod 이름 및 주소 관리
    """
    __tablename__ = "RUNPOD"
    
    # Primary Key
    RUNPOD_NO = Column(
        MySQL_BINARY(16),
        primary_key=True,
        nullable=False,
        comment="Runpod UUID (Primary Key)"
    )
    
    # Runpod Information
    NAME = Column(String(255), nullable=False, comment="Runpod 이름")
    ADDRESS = Column(String(500), nullable=False, comment="Runpod 주소")
    
    # Timestamps
    CREATED_AT = Column(DateTime, nullable=False, default=datetime.now, comment="생성 시간")
    UPDATED_AT = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now, comment="수정 시간")
    
    def __repr__(self):
        return f"<Runpod(RUNPOD_NO={self.RUNPOD_NO.hex() if self.RUNPOD_NO else None}, NAME={self.NAME}, ADDRESS={self.ADDRESS})>"

