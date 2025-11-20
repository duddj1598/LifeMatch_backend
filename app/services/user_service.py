from app.config.firebase_config import db
from app.schemas.user_schema import UserCreate
from datetime import datetime, timedelta
from fastapi import HTTPException
import jwt
import os

SECRET_KEY = os.getenv("JWT_SECRET", "your-secret-key")
ALGORITHM = "HS256"

def create_user(user: UserCreate):
    """
    (수정됨) 회원가입 로직 - 본인 확인 질문, 답변을 함께 저장
    """
    user_data = user.dict()
    user_data["created_at"] = datetime.utcnow()
  
    doc_ref = db.collection("users").document()
    doc_ref.set(user_data)
    return {"message": "회원가입 성공", "user_id": doc_ref.id}

def login_user(id: str, password: str):

    users_ref = db.collection("users")
    query_email = users_ref.where("user_email", "==", id).stream()
    query_id = users_ref.where("user_id", "==", id).stream()

    found_user = None
    for doc in query_email:
        found_user = doc.to_dict()
        break
    if not found_user:
        for doc in query_id:
            found_user = doc.to_dict()
            break

    if not found_user:
        raise HTTPException(status_code=404, detail="존재하지 않는 유저입니다.")

    survey_response = found_user.get("user_survey_response")
    has_completed_survey = survey_response is not None and len(survey_response) > 0

    if found_user["user_password"] != password:
        raise HTTPException(status_code=401, detail="비밀번호가 일치하지 않습니다.")

    payload = {
        "email": found_user.get("user_email"),
        "id": found_user.get("user_id"),
        "exp": datetime.utcnow() + timedelta(hours=12),  # 12시간 유효
        "nickname": found_user.get("user_nickname"),
    }
    access_token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    return {
        "status": 200,
        "accessToken": access_token,
        "nickname": found_user.get("user_nickname"),
        "hasCompletedSurvey": has_completed_survey
    }

'''(추가됨) 아이디 찾기 로직'''
def find_user_id(email: str, question: str, answer: str) -> str:

    users_ref = db.collection("users")
    query_email = users_ref.where("user_email", "==", email).limit(1).stream()

    found_user = None
    for doc in query_email:
        found_user = doc.to_dict()
        break

    if not found_user:
        raise HTTPException(status_code=404, detail="존재하지 않는 이메일입니다.")

    if (found_user.get("user_security_question") != question or
        found_user.get("user_security_answer") != answer):
        raise HTTPException(status_code=401, detail="본인 확인 정보가 일치하지 않습니다.")

    nickname = found_user.get("user_nickname")
    if not nickname:
        raise HTTPException(status_code=404, detail="닉네임 정보를 찾을 수 없습니다.")
    
    return nickname
'''(추가됨) 아이디 찾기 로직'''

'''(추가됨) 비밀번호 재설정 로직'''
def reset_password(login_id: str, email: str, question: str, answer: str, new_password: str):

    users_ref = db.collection("users")
    
    query_email = users_ref.where("user_email", "==", login_id).stream()
    query_nick = users_ref.where("user_nickname", "==", login_id).stream()

    found_user_doc = None
    found_user_data = None
    for doc in query_email:
        found_user_doc = doc
        found_user_data = doc.to_dict()
        break
    if not found_user_doc:
        for doc in query_nick:
            found_user_doc = doc
            found_user_data = doc.to_dict()
            break

    if not found_user_doc:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    if (found_user_data.get("user_email") != email or
        found_user_data.get("user_security_question") != question or
        found_user_data.get("user_security_answer") != answer):
        raise HTTPException(status_code=401, detail="본인 확인 정보가 일치하지 않습니다.")

    user_ref = users_ref.document(found_user_doc.id)
    user_ref.update({
        "user_password": new_password 
    })
    
    return True
'''(추가됨) 비밀번호 재설정 로직'''