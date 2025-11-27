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

#[추가] 그룹 정보 수정을 위한 Pydantic 모델
class GroupUpdateRequest(BaseModel):
    # 모든 필드는 Optional로 설정하여 부분 업데이트(PATCH)를 지원합니다.
    group_name: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None

    class Config:
        # 이 설정을 통해 업데이트할 데이터만 포함된 딕셔너리를 쉽게 생성할 수 있습니다.
        extra = "ignore"
