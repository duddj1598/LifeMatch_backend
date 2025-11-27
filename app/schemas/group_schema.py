from pydantic import BaseModel
from typing import Optional, List


class GroupCreate(BaseModel):
    group_name: str
    description: Optional[str] = None
    category: Optional[str] = None
    max_member: Optional[int] = 10
    group_image: Optional[str] = None


class GroupRead(GroupCreate):
    id: str
    created_at: Optional[str] = None  # ISO 포맷 문자열
    chat_id: Optional[str] = None
    leader_nickname: Optional[str] = None
    leader_id: Optional[str] = None
    current_member: Optional[int] = 0

    # ⭐⭐⭐ 팀원 목록 추가 (핵심)
    members: List[str] = []


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
    leader_interest: Optional[str]  # 팀장 관심사/유형
    group_image: Optional[str]
    leader_id: Optional[str]        # 팀장 ID


class GroupMember(BaseModel):
    user_id: str
    nickname: str
    profile_image: Optional[str]
