from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class BaseURLBase(BaseModel):
    service_name: str
    base_url: str

class BaseURLCreate(BaseURLBase):
    pass

class BaseURLUpdate(BaseModel):
    base_url: Optional[str] = None

class BaseURLResponse(BaseURLBase):
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class BaseURLSimple(BaseURLBase):
    """시간 정보를 제외한 간단한 Base URL 응답"""
    pass