from sqlalchemy import Column, DateTime, ForeignKey, LargeBinary, String
from app.core.database.base import Base
from app.core.utils.timezone_utils import now_kst


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
        default=now_kst,
        nullable=False,
    )
    updated_at = Column(
        "UPDATED_AT",
        DateTime,
        default=now_kst,
        onupdate=now_kst,
        nullable=False,
    )
