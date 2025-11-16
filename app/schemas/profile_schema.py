from pydantic import BaseModel
from typing import Optional, List, Dict

class ProfileUpdate(BaseModel):
    user_nickname: Optional[str] = None
    profile_image: Optional[str] = None
    activity_preferences: Optional[Dict[str, bool]] = None

class NotificationSettings(BaseModel):
    notification_enabled: bool

class LifestyleTypeInfo(BaseModel):
    """라이프스타일 유형 정보"""
    type_name: str
    keywords: str
    description: str

class ActivityReport(BaseModel):
    monthly_participation_count: int
    recent_participation_rate: float
    most_active_category: str

class ProfileResponse(BaseModel):
    user_nickname: str
    user_email: str
    profile_image: Optional[str] = None
    lifestyle_info: Optional[LifestyleTypeInfo] = None
    activity_report: Optional[ActivityReport] = None
    notification_settings: NotificationSettings
    activity_preferences: Optional[Dict[str, bool]] = None