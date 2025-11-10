"""
Ingest Group 모델
"""

from sqlalchemy import Column, DateTime, Boolean, LargeBinary, JSON, ForeignKey, String
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database.base import Base
import uuid


# ============================================
# UUID Helper Functions
# ============================================

def generate_uuid_binary() -> bytes:
    """UUID를 binary(16) 형식으로 생성"""
    return uuid.uuid4().bytes


def uuid_to_binary(uuid_str: str) -> bytes:
    """UUID 문자열을 binary(16)으로 변환"""
    return uuid.UUID(uuid_str).bytes


def binary_to_uuid(uuid_bytes: bytes) -> str:
    """binary(16)을 UUID 문자열로 변환"""
    return str(uuid.UUID(bytes=uuid_bytes))


# ============================================
# IngestGroup Model
# ============================================

class IngestGroup(Base):
    """Ingest 템플릿 그룹 테이블 (INGEST_GROUP)"""

    __tablename__ = "INGEST_GROUP"

    ingest_group_no = Column(
        "INGEST_GROUP_NO",
        LargeBinary(16),
        primary_key=True,
        default=generate_uuid_binary,
        nullable=False,
    )

    name = Column(
        "NAME",
        String(100),
        nullable=False,
    )

    is_default = Column(
        "IS_DEFAULT",
        Boolean,
        default=False,
        nullable=False,
    )

    chunking_strategy_no = Column(
        "CHUNKING_STRATEGY_NO",
        LargeBinary(16),
        ForeignKey("STRATEGY.STRATEGY_NO", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    chunking_parameter = Column(
        "CHUNKING_PARAMETER",
        JSON,
        nullable=False,
    )

    sparse_embedding_strategy_no = Column(
        "SPARSE_EMBEDDING_STRATEGY_NO",
        LargeBinary(16),
        ForeignKey("STRATEGY.STRATEGY_NO", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    sparse_embedding_parameter = Column(
        "SPARSE_EMBEDDING_PARAMETER",
        JSON,
        nullable=False,
    )

    created_at = Column(
        "CREATED_AT",
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at = Column(
        "UPDATED_AT",
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    chunking_strategy = relationship(
        "Strategy",
        foreign_keys=[chunking_strategy_no],
        lazy="selectin",
    )

    sparse_embedding_strategy = relationship(
        "Strategy",
        foreign_keys=[sparse_embedding_strategy_no],
        lazy="selectin",
    )

    extraction_groups = relationship(
        "ExtractionGroup",
        back_populates="ingest_group",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    embedding_groups = relationship(
        "EmbeddingGroup",
        back_populates="ingest_group",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self):
        return f"<IngestGroup(name={self.name}, is_default={self.is_default})>"


class ExtractionGroup(Base):
    """Extraction 템플릿 그룹 테이블 (EXTRACTION_GROUP)"""

    __tablename__ = "EXTRACTION_GROUP"

    extraction_group_no = Column(
        "EXTRACTION_GROUP_NO",
        LargeBinary(16),
        primary_key=True,
        default=generate_uuid_binary,
        nullable=False,
    )

    ingest_group_no = Column(
        "INGEST_GROUP_NO",
        LargeBinary(16),
        ForeignKey("INGEST_GROUP.INGEST_GROUP_NO", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    name = Column(
        "NAME",
        String(100),
        nullable=False,
    )

    extraction_strategy_no = Column(
        "EXTRACTION_STRATEGY_NO",
        LargeBinary(16),
        ForeignKey("STRATEGY.STRATEGY_NO", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    extraction_parameter = Column(
        "EXTRACTION_PARAMETER",
        JSON,
        nullable=False,
    )

    created_at = Column(
        "CREATED_AT",
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at = Column(
        "UPDATED_AT",
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    ingest_group = relationship(
        "IngestGroup",
        back_populates="extraction_groups",
        lazy="selectin",
    )

    extraction_strategy = relationship(
        "Strategy",
        foreign_keys=[extraction_strategy_no],
        lazy="selectin",
    )

    def __repr__(self):
        return f"<ExtractionGroup(name={self.name})>"


class EmbeddingGroup(Base):
    """Embedding 템플릿 그룹 테이블 (EMBEDDING_GROUP)"""

    __tablename__ = "EMBEDDING_GROUP"

    embedding_group_no = Column(
        "EMBEDDING_GROUP_NO",
        LargeBinary(16),
        primary_key=True,
        default=generate_uuid_binary,
        nullable=False,
    )

    ingest_group_no = Column(
        "INGEST_GROUP_NO",
        LargeBinary(16),
        ForeignKey("INGEST_GROUP.INGEST_GROUP_NO", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    name = Column(
        "NAME",
        String(100),
        nullable=False,
    )

    embedding_strategy_no = Column(
        "EMBEDDING_STRATEGY_NO",
        LargeBinary(16),
        ForeignKey("STRATEGY.STRATEGY_NO", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    embedding_parameter = Column(
        "EMBEDDING_PARAMETER",
        JSON,
        nullable=False,
    )

    created_at = Column(
        "CREATED_AT",
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at = Column(
        "UPDATED_AT",
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    ingest_group = relationship(
        "IngestGroup",
        back_populates="embedding_groups",
        lazy="selectin",
    )

    embedding_strategy = relationship(
        "Strategy",
        foreign_keys=[embedding_strategy_no],
        lazy="selectin",
    )

    def __repr__(self):
        return f"<EmbeddingGroup(name={self.name})>"
