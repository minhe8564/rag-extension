from __future__ import annotations

import uuid
from datetime import datetime
from sqlalchemy import String, text 
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.mysql import BINARY, DATETIME as MySQLDateTime
from app.core.base import Base


class FileCategory(Base):
    __tablename__ = "FILE_CATEGORY"

    file_category_no: Mapped[bytes] = mapped_column(
        "FILE_CATEGORY_NO", BINARY(16), primary_key=True, server_default=text("UUID_TO_BIN(UUID())"),
    )
    name: Mapped[str] = mapped_column("NAME", String(50), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column("CREATED_AT", MySQLDateTime(fsp=6), nullable=False)
    updated_at: Mapped[datetime] = mapped_column("UPDATED_AT", MySQLDateTime(fsp=6), nullable=False)

    # Convenience: serialize primary key as hex string
    def pk_hex(self) -> str:
        return self.file_category_no.hex() if isinstance(self.file_category_no, (bytes, bytearray)) else str(self.file_category_no)
