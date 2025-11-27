from pydantic import BaseModel

class GroupInviteRequest(BaseModel):
    group_id: str

class GroupInviteResponse(BaseModel):
    status: int
    message: str
    action_id: str


class GroupApplyRequest(BaseModel):
    group_id: str

class GroupApplyResponse(BaseModel):
    status: int
    message: str
    action_id: str
