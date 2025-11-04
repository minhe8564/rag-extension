"""
OFFER 테이블 모델
"""
from sqlalchemy import Column, Integer, DateTime, CHAR
from sqlalchemy.dialects.mysql import CHAR as MySQL_CHAR
from datetime import datetime
from app.core.base import Base


class Offer(Base):
    __tablename__ = "OFFER"
    
    # Primary Key
    offer_no = Column(
        "OFFER_NO",
        MySQL_CHAR(10),
        primary_key=True
    )
    
    # Offer Information
    version = Column("VERSION", Integer, nullable=False, comment="1, 2")
    
    # Timestamps
    created_at = Column("CREATED_AT", DateTime(6), nullable=False)
    updated_at = Column("UPDATED_AT", DateTime(6), nullable=False)
    
    def __repr__(self):
        return f"<Offer(offer_no={self.offer_no}, version={self.version})>"
