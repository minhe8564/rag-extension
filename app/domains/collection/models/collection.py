from __future__ import annotations

from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.mysql import BINARY, CHAR, DATETIME as MySQLDateTime

from app.core.base import Base


class Collection(Base):
    __tablename__ = "COLLECTION"

    collection_no: Mapped[bytes] = mapped_column("COLLECTION_NO", BINARY(16), primary_key=True)
    offer_no: Mapped[str] = mapped_column("OFFER_NO", CHAR(10), nullable=False)
    created_at: Mapped[datetime] = mapped_column("CREATED_AT", MySQLDateTime(fsp=6), nullable=False)
    updated_at: Mapped[datetime] = mapped_column("UPDATED_AT", MySQLDateTime(fsp=6), nullable=False)

