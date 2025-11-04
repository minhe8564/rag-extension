"""
USER 테이블 모델
"""
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, CHAR, BINARY
from sqlalchemy.dialects.mysql import BINARY as MySQL_BINARY, CHAR as MySQL_CHAR
from datetime import datetime
from app.core.base import Base


class User(Base):
    __tablename__ = "USER"
    
    # Primary Key
    user_no = Column(
        "USER_NO",
        MySQL_BINARY(16),
        primary_key=True
    )
    
    # User Information
    email = Column("EMAIL", String(254), nullable=False, unique=True)
    password = Column("PASSWORD", String(255), nullable=False)
    name = Column("NAME", String(50), nullable=False)
    
    # Foreign Keys
    user_role_no = Column(
        "USER_ROLE_NO",
        MySQL_BINARY(16),
        ForeignKey("USER_ROLE.USER_ROLE_NO"),
        nullable=False,
        index=True
    )
    
    offer_no = Column(
        "OFFER_NO",
        MySQL_CHAR(10),
        ForeignKey("OFFER.OFFER_NO"),
        nullable=False,
        index=True
    )
    
    # Business Type: 0=개인 안경원, 1=체인 안경원, 2=제조 유통사
    business_type = Column("BUSINESS_TYPE", Integer, nullable=False)
    
    # Timestamps
    created_at = Column("CREATED_AT", DateTime, nullable=False)
    updated_at = Column("UPDATED_AT", DateTime, nullable=False)
    deleted_at = Column("DELETED_AT", DateTime, nullable=True)
    
    def __repr__(self):
        return f"<User(user_no={self.user_no.hex if self.user_no else None}, email={self.email}, name={self.name})>"
