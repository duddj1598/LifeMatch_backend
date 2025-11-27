from pydantic import BaseModel
from typing import List, Optional

class RecommendedActivity(BaseModel):
    group_id: str
    group_name: str
    category: Optional[str] = None
    leader_id: Optional[str] = None

class HomeData(BaseModel):
    user_lifestyle_type: str
    recommended_activities: List[RecommendedActivity]

class HomeResponse(BaseModel):
    status: int
    data: HomeData

# --- ▼ (추가된 부분) ---

class OtherRecommendationsResponse(BaseModel):
    """
    '다른 유형' 추천 활동 목록을 위한 응답 스키마
    """
    status: int
    data: List[RecommendedActivity]
# --- ▲ (추가된 부분) ---