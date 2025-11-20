from pydantic import BaseModel, EmailStr
from typing import Optional

class UserCreate(BaseModel):
    user_email: EmailStr
    user_id : str
    user_nickname: str
    user_password: str
    user_joined_groups_id: Optional[int] = None
    user_owned_groups_id: Optional[int] = None
    user_lifestyle_type: Optional[str] = None