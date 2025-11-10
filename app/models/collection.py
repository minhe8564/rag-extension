from sqlalchemy import Column, String, Integer, DateTime, func
from sqlalchemy.dialects.mysql import BINARY
from app.models.database import Base
import uuid


class Collection(Base):
    """COLLECTION 테이블 모델"""
    __tablename__ = "COLLECTION"
    
    COLLECTION_NO = Column(BINARY(16), primary_key=True, nullable=False)
    OFFER_NO = Column(String(10), nullable=False)
    NAME = Column(String(255), nullable=False, unique=True)
    VERSION = Column(Integer, nullable=False, default=1)
    INGEST_GROUP_NO = Column(BINARY(16), nullable=False)
    CREATED_AT = Column(DateTime, nullable=False, default=func.now())
    UPDATED_AT = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<Collection(COLLECTION_NO={self.COLLECTION_NO.hex() if isinstance(self.COLLECTION_NO, bytes) else 'N/A'}, NAME={self.NAME})>"

