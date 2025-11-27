from pydantic import BaseModel, EmailStr
from typing import Optional, List

class UserCreate(BaseModel):
    user_email: EmailStr
    user_id : str
    user_nickname: str
    user_password: str
    user_security_question: str
    user_security_answer: str

'''추가됨'''
class FindIdRequest(BaseModel):
    user_nickname: str
    security_question: str
    security_answer: str

class FindIdResponse(BaseModel):
    status: int
    user_id: str

class ResetPasswordRequest(BaseModel):
    login_id: str
    security_question: str
    security_answer: str
    new_password: str
'''추가됨'''

class MyGroup(BaseModel):
    group_id: str
    group_name: str
    category: Optional[str]
    current_member: int
    max_member: int
    description: Optional[str]
    group_image: Optional[str]

class MyGroupListResponse(BaseModel):
    status: int
    groups: List[MyGroup]
