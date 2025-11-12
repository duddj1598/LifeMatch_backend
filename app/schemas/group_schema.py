from pydantic import BaseModel
from typing import Optional

class GroupCreate(BaseModel):
    group_name: str
    description: Optional[str] = None
    category: Optional[str] = None
    max_member: Optional[int] = 10

class GroupRead(BaseModel):
    id: str
    group_name: str
    description: Optional[str] = None
    category: Optional[str] = None
    max_member: int

    class Config:
        orm_mode = True
