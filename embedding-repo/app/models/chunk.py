from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, func
from sqlalchemy.dialects.mysql import BINARY
from app.models.database import Base
import uuid


class Chunk(Base):
    """CHUNK 테이블 모델"""
    __tablename__ = "CHUNK"
    
    CHUNK_NO = Column(BINARY(16), primary_key=True, nullable=False)
    COLLECTION_NO = Column(BINARY(16), ForeignKey("COLLECTION.COLLECTION_NO"), nullable=False)
    FILE_NO = Column(BINARY(16), nullable=False)
    FILE_NAME = Column(String(255), nullable=False)
    PAGE_NO = Column(Integer, nullable=False)
    INDEX_NO = Column(Integer, nullable=False)
    CREATED_AT = Column(DateTime, nullable=False, default=func.now())
    UPDATED_AT = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        chunk_no_hex = self.CHUNK_NO.hex() if isinstance(self.CHUNK_NO, bytes) else 'N/A'
        return f"<Chunk(CHUNK_NO={chunk_no_hex}, FILE_NAME={self.FILE_NAME}, PAGE_NO={self.PAGE_NO}, INDEX_NO={self.INDEX_NO})>"

