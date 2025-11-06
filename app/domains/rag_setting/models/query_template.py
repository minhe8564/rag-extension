"""
Query Group 모델
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
# QueryGroup Model
# ============================================

class QueryGroup(Base):
    """
    Query 템플릿 그룹 테이블 (QUERY_GROUP)
    Transformation, Retrieval, Reranking, Prompting, Generation 전략을 조합한 템플릿
    """
    __tablename__ = "QUERY_GROUP"

    # Python 속성은 소문자, DB 컬럼은 대문자로 명시
    query_group_no = Column(
        "QUERY_GROUP_NO",
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

    # 외래 키: Transformation 전략
    transformation_strategy_no = Column(
        "TRANSFORMATION_STRATEGY_NO",
        LargeBinary(16),
        ForeignKey("STRATEGY.STRATEGY_NO", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # 외래 키: Retrieval 전략
    retrieval_strategy_no = Column(
        "RETRIEVAL_STRATEGY_NO",
        LargeBinary(16),
        ForeignKey("STRATEGY.STRATEGY_NO", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # 외래 키: Reranking 전략
    reranking_strategy_no = Column(
        "RERANKING_STRATEGY_NO",
        LargeBinary(16),
        ForeignKey("STRATEGY.STRATEGY_NO", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # 외래 키: System Prompting 전략
    system_prompting_strategy_no = Column(
        "SYSTEM_PROMPTING_STRATEGY_NO",
        LargeBinary(16),
        ForeignKey("STRATEGY.STRATEGY_NO", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # 외래 키: User Prompting 전략
    user_prompting_strategy_no = Column(
        "USER_PROMPTING_STRATEGY_NO",
        LargeBinary(16),
        ForeignKey("STRATEGY.STRATEGY_NO", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # 외래 키: Generation 전략
    generation_strategy_no = Column(
        "GENERATION_STRATEGY_NO",
        LargeBinary(16),
        ForeignKey("STRATEGY.STRATEGY_NO", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # JSON 파라미터
    transformation_parameter = Column(
        "TRANSFORMATION_PARAMETER",
        JSON,
        nullable=False
    )

    retrieval_parameter = Column(
        "RETRIEVAL_PARAMETER",
        JSON,
        nullable=False
    )

    reranking_parameter = Column(
        "RERANKING_PARAMETER",
        JSON,
        nullable=False
    )

    system_prompting_parameter = Column(
        "SYSTEM_PROMPTING_PARAMETER",
        JSON,
        nullable=False
    )

    user_prompting_parameter = Column(
        "USER_PROMPTING_PARAMETER",
        JSON,
        nullable=False
    )

    generation_parameter = Column(
        "GENERATION_PARAMETER",
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

    # 관계 정의: QueryGroup → Strategy (N:1)
    transformation_strategy = relationship(
        "Strategy",
        foreign_keys=[transformation_strategy_no],
        lazy="selectin"
    )

    retrieval_strategy = relationship(
        "Strategy",
        foreign_keys=[retrieval_strategy_no],
        lazy="selectin"
    )

    reranking_strategy = relationship(
        "Strategy",
        foreign_keys=[reranking_strategy_no],
        lazy="selectin"
    )

    system_prompting_strategy = relationship(
        "Strategy",
        foreign_keys=[system_prompting_strategy_no],
        lazy="selectin"
    )

    user_prompting_strategy = relationship(
        "Strategy",
        foreign_keys=[user_prompting_strategy_no],
        lazy="selectin"
    )

    generation_strategy = relationship(
        "Strategy",
        foreign_keys=[generation_strategy_no],
        lazy="selectin"
    )

    def __repr__(self):
        return f"<QueryGroup(name={self.name}, is_default={self.is_default})>"
