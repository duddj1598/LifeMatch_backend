from pydantic import BaseModel, EmailStr
from typing import Optional, List

class UserCreate(BaseModel):
    user_email: EmailStr
    user_id : str
    user_nickname: str
    user_password: str

    '''(추가됨)본인 확인 질문/답변 저장용 필드'''
    user_security_question: str
    user_security_answer: str
    '''(추가됨)본인 확인 질문/답변 저장용 필드'''

    user_lifestyle_vector: Optional[list] = []
    user_joined_groups_id: Optional[int] = None
    user_owned_groups_id: Optional[int] = None
    panel_id: Optional[int] = None
    user_lifestyle_type: Optional[str] = None

'''추가됨'''
class FindIdRequest(BaseModel):
    user_email: EmailStr
    security_question: str
    security_answer: str

class FindIdResponse(BaseModel):
    status: int
    user_nickname: str

class ResetPasswordRequest(BaseModel):
    login_id: str
    user_email: EmailStr
    security_question: str
    security_answer: str
    new_password: str
'''추가됨'''
