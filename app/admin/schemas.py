from pydantic import BaseModel
from datetime import datetime

class RunPodBase(BaseModel):
    api_url: str

class RunPodUpdate(RunPodBase):
    pass

class RunPodResponse(RunPodBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class RunPodUrlOnly(BaseModel):
    api_url: str
    
    class Config:
        from_attributes = True
