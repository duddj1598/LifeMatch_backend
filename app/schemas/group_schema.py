from pydantic import BaseModel
from typing import Optional, List

class GroupCreate(BaseModel):
    group_name: str
    description: Optional[str] = None
    category: Optional[str] = None
    max_member: Optional[int] = 10
    leader_id: Optional[str] = None
    group_image: Optional[str] = None  # 이미지 URL

class GroupUpdate(BaseModel):
    group_name: Optional[str]
    description: Optional[str]
    category: Optional[str]
    group_image: Optional[str]

class GroupListResponse(BaseModel):
    group_name: str
    category: str
    max_member: int
    current_member: int

class GroupDetailResponse(BaseModel):
    group_name: str
    category: str
    max_member: int
    current_member: int
    description: Optional[str]
    leader_nickname: Optional[str]
    group_image: Optional[str]

class GroupMember(BaseModel):
    user_id: str
    nickname: str
    profile_image: Optional[str]
