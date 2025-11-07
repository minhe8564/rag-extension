from __future__ import annotations

from datetime import datetime
from sqlalchemy import Column, DateTime, LargeBinary, String, Integer, Text
from app.core.base import Base


class TestFile(Base):
    __tablename__ = "TEST_FILE"

    test_file_no = Column(
        "TEST_FILE_NO",
        LargeBinary(16),
        primary_key=True,
        nullable=False,
    )

    name = Column("NAME", String(255), nullable=False)
    size = Column("SIZE", Integer, nullable=False)
    type = Column("TYPE", String(20), nullable=False)
    hash = Column("HASH", String(255), nullable=False)
    description = Column("DESCRIPTION", Text, nullable=False)
    bucket = Column("BUCKET", String(255), nullable=False)
    path = Column("PATH", String(255), nullable=False)

    created_at = Column("CREATED_AT", DateTime, nullable=False)
    updated_at = Column("UPDATED_AT", DateTime, nullable=False)

    source_no = Column("SOURCE_NO", LargeBinary(16), nullable=False)

