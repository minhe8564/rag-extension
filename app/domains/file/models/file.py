from __future__ import annotations

from datetime import datetime
from sqlalchemy import String, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.mysql import BINARY, CHAR, DATETIME as MySQLDateTime

from ....common.db import Base


class File(Base):
    __tablename__ = "FILE"

    file_no: Mapped[bytes] = mapped_column("FILE_NO", BINARY(16), primary_key=True)
    user_no: Mapped[bytes] = mapped_column("USER_NO", BINARY(16), nullable=False)
    name: Mapped[str] = mapped_column("NAME", String(255), nullable=False)
    size: Mapped[int] = mapped_column("SIZE", Integer, nullable=False)
    type: Mapped[str] = mapped_column("TYPE", String(20), nullable=False)
    hash: Mapped[str] = mapped_column("HASH", String(255), nullable=False)
    description: Mapped[str] = mapped_column("DESCRIPTION", Text, nullable=False)
    bucket: Mapped[str] = mapped_column("BUCKET", String(255), nullable=False)
    path: Mapped[str] = mapped_column("PATH", String(255), nullable=False)
    file_category_no: Mapped[bytes] = mapped_column("FILE_CATEGORY_NO", BINARY(16), nullable=False)
    offer_no: Mapped[str] = mapped_column("OFFER_NO", CHAR(10), nullable=False)
    source_no: Mapped[bytes | None] = mapped_column("SOURCE_NO", BINARY(16), nullable=True)
    collection_no: Mapped[bytes | None] = mapped_column("COLLECTION_NO", BINARY(16), nullable=True)
    created_at: Mapped[datetime] = mapped_column("CREATED_AT", MySQLDateTime(fsp=6), nullable=False)
    updated_at: Mapped[datetime] = mapped_column("UPDATED_AT", MySQLDateTime(fsp=6), nullable=False)

