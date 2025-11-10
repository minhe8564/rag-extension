from typing import List, Optional
from pydantic import BaseModel

class CollectionRequest(BaseModel):
    name: Optional[str] = None
    numberList: Optional[List[int]] = None