from pydantic import BaseModel, EmailStr
from typing import Optional

class UserCreate(BaseModel):
    user_email: EmailStr
    user_nickname: str
    user_password: str
    user_lifestyle_vector: Optional[list] = []
    user_survey_response: Optional[dict] = {}
    user_joined_groups_id: Optional[int] = None
    user_owned_groups_id: Optional[int] = None
    panel_id: Optional[int] = None
