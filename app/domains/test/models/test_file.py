from __future__ import annotations

from datetime import datetime
from sqlalchemy import Column, DateTime, LargeBinary, String, Integer, Text, ForeignKey
from app.core.database.base import Base


class TestFile(Base):
    __tablename__ = "TEST_FILE"

    test_file_no = Column(
        "TEST_FILE_NO",
        LargeBinary(16),
        primary_key=True,
        nullable=False,
    )

    test_collection_no = Column(
        "TEST_COLLECTION_NO",
        LargeBinary(16),
        ForeignKey(
            "TEST_COLLECTION.TEST_COLLECTION_NO",
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
        comment="테스트 컬렉션 참조",
    )

    name = Column("NAME", String(255), nullable=False)
    size = Column("SIZE", Integer, nullable=False)
    type = Column("TYPE", String(20), nullable=False)
    hash = Column("HASH", String(255), nullable=False)
    description = Column("DESCRIPTION", Text, nullable=False)
    bucket = Column("BUCKET", String(255), nullable=False)
    path = Column("PATH", String(255), nullable=False)
    status = Column("STATUS", String(20), nullable=False, default="PENDING", server_default="PENDING", index=True)

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

    source_no = Column("SOURCE_NO", LargeBinary(16), nullable=False)

