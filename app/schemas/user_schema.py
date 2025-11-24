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
    user_email: EmailStr
    security_question: str
    security_answer: str

class FindIdResponse(BaseModel):
    status: int
    user_id: str

class ResetPasswordRequest(BaseModel):
    login_id: str
    user_email: EmailStr
    security_question: str
    security_answer: str
    new_password: str
'''추가됨'''
