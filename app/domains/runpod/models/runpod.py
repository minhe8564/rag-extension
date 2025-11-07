"""
RUNPOD 테이블 모델
Runpod 이름 및 주소를 저장하는 모델
"""

from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.mysql import BINARY as MySQL_BINARY
from datetime import datetime
import uuid
from app.core.base import Base


class Runpod(Base):
    """
    RUNPOD 테이블 모델
    Runpod 이름 및 주소 관리
    """
    __tablename__ = "RUNPOD"
    
    # Primary Key
    runpod_no = Column(
        "RUNPOD_NO",
        MySQL_BINARY(16),
        primary_key=True,
        default=lambda: uuid.uuid4().bytes
    )
    
    # Runpod Information
    name = Column("NAME", String(255), nullable=False, comment="Runpod 이름")
    address = Column("ADDRESS", String(500), nullable=False, comment="Runpod 주소")
    
    # Timestamps
    created_at = Column("CREATED_AT", DateTime, nullable=False, default=datetime.now)
    updated_at = Column("UPDATED_AT", DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    
    def __repr__(self):
        return f"<Runpod(runpod_no={self.runpod_no.hex() if self.runpod_no else None}, name={self.name}, address={self.address})>"

