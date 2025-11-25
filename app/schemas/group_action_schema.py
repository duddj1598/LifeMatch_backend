from pydantic import BaseModel

class GroupInviteRequest(BaseModel):
    group_id: str
    user_id: str   # 프론트 내부 user_id

class GroupInviteResponse(BaseModel):
    status: int
    message: str
    action_id: str


class GroupApplyRequest(BaseModel):
    group_id: str
    user_id: str   # 신청하는 유저의 내부 user_id

class GroupApplyResponse(BaseModel):
    status: int
    message: str
    action_id: str
