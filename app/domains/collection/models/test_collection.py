from sqlalchemy import Column, DateTime, ForeignKey, LargeBinary, String
from datetime import datetime
from app.core.base import Base


class TestCollection(Base):
    __tablename__ = "TEST_COLLECTION"

    test_collection_no = Column(
        "TEST_COLLECTION_NO",
        LargeBinary(16),
        primary_key=True,
        nullable=False,
    )
    name = Column("NAME", String(255), nullable=False)
    ingest_group_no = Column(
        "INGEST_GROUP_NO",
        LargeBinary(16),
        ForeignKey("INGEST_GROUP.INGEST_GROUP_NO", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
        index=True,
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
