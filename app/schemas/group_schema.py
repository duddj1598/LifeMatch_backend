from pydantic import BaseModel
from typing import Optional

class GroupCreate(BaseModel):
    group_name: str
    description: Optional[str] = None
    category: Optional[str] = None
    max_member: Optional[int] = 10
    