"""
RAG Strategy 모델
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, LargeBinary
from sqlalchemy.orm import relationship
from app.core.database.base import Base
from app.core.utils.timezone_utils import now_kst
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
# StrategyType Model
# ============================================

class StrategyType(Base):
    """
    전략 유형 테이블 (STRATEGY_TYPE)
    - extraction, chunking, embedding, transformation,
      retrieval, reranking, prompting, generation
    """
    __tablename__ = "STRATEGY_TYPE"

    # Python 속성은 소문자, DB 컬럼은 대문자로 명시
    strategy_type_no = Column(
        "STRATEGY_TYPE_NO",
        LargeBinary(16),
        primary_key=True,
        default=generate_uuid_binary,
        nullable=False
    )

    name = Column(
        "NAME",
        String(255),
        nullable=False,
        unique=True,
        index=True
    )

    created_at = Column(
        "CREATED_AT",
        DateTime,
        default=now_kst,
        nullable=False
    )

    updated_at = Column(
        "UPDATED_AT",
        DateTime,
        default=now_kst,
        onupdate=now_kst,
        nullable=False
    )

    # 관계 정의: StrategyType → Strategy (1:N)
    strategies = relationship(
        "Strategy",
        back_populates="strategy_type",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<StrategyType(name='{self.name}')>"


# ============================================
# Strategy Model
# ============================================

class Strategy(Base):
    """
    RAG 전략 테이블 (STRATEGY)
    각 전략은 하나의 StrategyType에 속함
    """
    __tablename__ = "STRATEGY"

    # Python 속성은 소문자, DB 컬럼은 대문자로 명시
    strategy_no = Column(
        "STRATEGY_NO",
        LargeBinary(16),
        primary_key=True,
        default=generate_uuid_binary,
        nullable=False
    )

    strategy_type_no = Column(
        "STRATEGY_TYPE_NO",
        LargeBinary(16),
        ForeignKey("STRATEGY_TYPE.STRATEGY_TYPE_NO", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )

    name = Column(
        "NAME",
        String(50),
        nullable=False,
        index=True
    )

    code = Column(
        "CODE",
        String(255),
        nullable=False,
        index=True,
    )

    description = Column(
        "DESCRIPTION",
        String(255),
        nullable=False
    )

    parameter = Column(
        "PARAMETER",
        JSON,
        nullable=True
    )

    created_at = Column(
        "CREATED_AT",
        DateTime,
        default=now_kst,
        nullable=False
    )

    updated_at = Column(
        "UPDATED_AT",
        DateTime,
        default=now_kst,
        onupdate=now_kst,
        nullable=False
    )

    # 관계 정의: Strategy → StrategyType (N:1)
    strategy_type = relationship(
        "StrategyType",
        back_populates="strategies"
    )

    def __repr__(self):
        return f"<Strategy(name='{self.name}', type='{self.strategy_type.name if self.strategy_type else None}')>"
