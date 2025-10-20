from sqlalchemy import Column, Integer, Text, DateTime
from datetime import datetime
from ..database import Base

class RunPod(Base):
    __tablename__ = "runpod"
    
    id = Column(Integer, primary_key=True, index=True)
    api_url = Column(Text, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
