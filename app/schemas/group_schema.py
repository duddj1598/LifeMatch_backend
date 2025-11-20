from pydantic import BaseModel
from typing import Optional, List

class GroupCreate(BaseModel):
    group_name: str
    description: Optional[str] = None
    category: Optional[str] = None
    max_member: Optional[int] = 10
    leader_id: Optional[str] = None
    group_image: Optional[str] = None

class GroupRead(GroupCreate):
    id: str
    created_at: Optional[str] = None # ISO 포맷 문자열로 변환하여 저장하므로 str
    chat_id: Optional[str] = None

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
    leader_interest: Optional[str]  #팀장 관심사/유형 추가
    group_image: Optional[str]
    leader_id: Optional[str]        #팀장 ID 추가

class GroupMember(BaseModel):
    user_id: str
    nickname: str
    profile_image: Optional[str]
