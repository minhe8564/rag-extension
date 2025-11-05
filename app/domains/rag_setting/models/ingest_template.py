"""
Ingest Group 모델
"""

from sqlalchemy import Column, DateTime, Boolean, LargeBinary, JSON, ForeignKey, String
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.base import Base
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
    """
    Ingest 템플릿 그룹 테이블 (INGEST_GROUP)
    추출, 청킹, 임베딩 전략을 조합한 템플릿
    """
    __tablename__ = "INGEST_GROUP"

    # Python 속성은 소문자, DB 컬럼은 대문자로 명시
    ingest_group_no = Column(
        "INGEST_GROUP_NO",
        LargeBinary(16),
        primary_key=True,
        default=generate_uuid_binary,
        nullable=False
    )

    name = Column(
        "NAME",
        String(100),
        nullable=False
    )

    is_default = Column(
        "IS_DEFAULT",
        Boolean,
        default=False,
        nullable=False
    )

    # 외래 키: Extraction 전략
    extraction_strategy_no = Column(
        "EXTRACTION_STRATEGY_NO",
        LargeBinary(16),
        ForeignKey("STRATEGY.STRATEGY_NO", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # 외래 키: Chunking 전략
    chunking_strategy_no = Column(
        "CHUNKING_STRATEGY_NO",
        LargeBinary(16),
        ForeignKey("STRATEGY.STRATEGY_NO", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # 외래 키: Embedding 전략
    embedding_strategy_no = Column(
        "EMBEDDING_STRATEGY_NO",
        LargeBinary(16),
        ForeignKey("STRATEGY.STRATEGY_NO", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # JSON 파라미터
    extraction_parameter = Column(
        "EXTRACTION_PARAMETER",
        JSON,
        nullable=False
    )

    chunking_parameter = Column(
        "CHUNKING_PARAMETER",
        JSON,
        nullable=False
    )

    embedding_parameter = Column(
        "EMBEDDING_PARAMETER",
        JSON,
        nullable=False
    )

    created_at = Column(
        "CREATED_AT",
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    updated_at = Column(
        "UPDATED_AT",
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # 관계 정의: IngestGroup → Strategy (N:1)
    extraction_strategy = relationship(
        "Strategy",
        foreign_keys=[extraction_strategy_no],
        lazy="selectin"
    )

    chunking_strategy = relationship(
        "Strategy",
        foreign_keys=[chunking_strategy_no],
        lazy="selectin"
    )

    embedding_strategy = relationship(
        "Strategy",
        foreign_keys=[embedding_strategy_no],
        lazy="selectin"
    )

    def __repr__(self):
        return f"<IngestGroup(is_default={self.is_default})>"
