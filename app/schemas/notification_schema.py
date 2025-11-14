from pydantic import BaseModel
from typing import Optional, List

class RespondToAction(BaseModel):
    user_id: str
    action: str

class NotificationBase(BaseModel):
    action_id: str
    group_id: str
    group_name: str
    group_image: Optional[str] = None

class GroupInviteNotification(NotificationBase):
    group_subject: Optional[str] #ex) 주제: 투자·소비습관

class GroupApplicantNotification(NotificationBase):
    applicant_id: str
    applicant_nickname: str
    applicant_interest: Optional[str] #ex) 관심사: 유저 관심사

class NotificationsListResponse(BaseModel):
    status: int
    invites: List[GroupInviteNotification]
    applicants: List[GroupApplicantNotification]