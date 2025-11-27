from app.config.firebase_config import db
from app.schemas.user_schema import UserCreate
from datetime import datetime, timedelta
from fastapi import HTTPException
import jwt
import os
from google.cloud.firestore_v1 import FieldFilter

SECRET_KEY = os.getenv("JWT_SECRET", "your-secret-key")
ALGORITHM = "HS256"


#중복확인
def is_id_duplicate(user_id: str) -> bool:
    """아이디 중복 검사: 존재하면 True"""
    users_ref = db.collection("users")
    docs = users_ref.where("user_id", "==", user_id).limit(1).stream()
    return any(docs)

def is_nickname_duplicate(nickname: str) -> bool:
    """닉네임 중복 검사: 존재하면 True"""
    users_ref = db.collection("users")
    docs = users_ref.where("user_nickname", "==", nickname).limit(1).stream()
    return any(docs)

def is_email_duplicate(email: str) -> bool:
    """이메일 중복 검사: 존재하면 True"""
    users_ref = db.collection("users")
    docs = users_ref.where("user_email", "==", email).limit(1).stream()
    return any(docs)


#회원가입
def create_user(user: UserCreate):
    if is_id_duplicate(user.user_id):
        raise HTTPException(status_code=409, detail="이미 사용 중인 아이디입니다.")

    if is_email_duplicate(user.user_email):
        raise HTTPException(status_code=409, detail="이미 가입된 이메일입니다.")
        
    if is_nickname_duplicate(user.user_nickname):
        raise HTTPException(status_code=409, detail="이미 사용 중인 닉네임입니다.")

    user_data = user.dict()
    user_data["created_at"] = datetime.utcnow()

    user_ref = db.collection("users").document()
    user_ref.set(user_data)

    return {
        "status": 201,
        "message": "회원가입 성공",
        "user_id": user_ref.id
    }

def login_user(login_id: str, password: str):
    users_ref = db.collection("users")

    query_email = users_ref.where("user_email", "==", login_id).stream()
    query_login = users_ref.where("user_id", "==", login_id).stream()

    found_doc = None
    found_user = None

    for doc in query_email:
        found_doc = doc
        found_user = doc.to_dict()
        break

    if not found_user:
        for doc in query_login:
            found_doc = doc
            found_user = doc.to_dict()
            break

    if not found_user:
        raise HTTPException(status_code=404, detail="존재하지 않는 유저입니다.")

    if found_user["user_password"] != password:
        raise HTTPException(status_code=401, detail="비밀번호가 일치하지 않습니다.")

    survey_response = found_user.get("user_survey_response")
    has_completed_survey = survey_response is not None and len(survey_response) > 0

    user_doc_id = found_doc.id

    payload = {
        "sub": user_doc_id,
        "email": found_user.get("user_email"),
        "login_id": found_user.get("user_id"),
        "nickname": found_user.get("user_nickname"),
        "exp": datetime.utcnow() + timedelta(hours=12)
    }

    access_token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    return {
        "status": 200,
        "accessToken": access_token,
        "nickname": found_user.get("user_nickname"),
        "hasCompletedSurvey": has_completed_survey
    }


def find_user_id(email: str, question: str, answer: str) -> str:
    users_ref = db.collection("users")
    query_ref = users_ref.where(filter=FieldFilter('user_email', '==', email))
    
    found_user = None
    query = query_ref.get()
    for doc in query:
        found_user = doc.to_dict()
        break

    if not found_user:
        raise HTTPException(status_code=404, detail="존재하지 않는 이메일입니다.")

    if (
        found_user.get("user_security_question") != question or
        found_user.get("user_security_answer") != answer
    ):
        raise HTTPException(status_code=401, detail="본인 확인 정보가 일치하지 않습니다.")
    return found_user.get("user_id")


def reset_password(login_id: str, email: str, question: str, answer: str, new_password: str):
    users_ref = db.collection("users")

    query_email = users_ref.where("user_email", "==", login_id).stream()
    query_nick = users_ref.where("user_id", "==", login_id).stream()

    found_doc = None
    found_user = None

    for doc in query_email:
        found_doc = doc
        found_user = doc.to_dict()
        break

    if not found_doc:
        for doc in query_nick:
            found_doc = doc
            found_user = doc.to_dict()
            break

    if not found_doc:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    if (
        found_user.get("user_email") != email or
        found_user.get("user_security_question") != question or
        found_user.get("user_security_answer") != answer
    ):
        raise HTTPException(status_code=401, detail="본인 확인 정보가 일치하지 않습니다.")

    db.collection("users").document(found_doc.id).update({
        "user_password": new_password
    })

    return True


def get_managed_groups(user_doc_id: str):
    """
    내가 리더인 그룹 조회 (leader_id == user_doc_id)
    """
    try:
        group_ref = db.collection("groups").where(
            "leader_id", "==", user_doc_id
        ).stream()

        groups = []
        for doc in group_ref:
            data = doc.to_dict()
            groups.append({
                "group_id": doc.id,
                "group_name": data.get("group_name"),
                "category": data.get("category"),
                "current_member": data.get("current_member", 0),
                "max_member": data.get("max_member", 10),
                "description": data.get("description"),
                "group_image": data.get("group_image"),
            })

        return {
            "status": 200,
            "groups": groups
        }

    except Exception as e:
        print("[get_managed_groups]", e)
        raise HTTPException(status_code=500, detail="관리 소모임 조회 오류")


def get_joined_groups(user_doc_id: str):
    """
    내가 참여한 그룹 조회 (members 배열에 포함)
    """
    try:
        group_ref = db.collection("groups").where(
            "members", "array_contains", user_doc_id
        ).stream()

        groups = []
        for doc in group_ref:
            data = doc.to_dict()
            groups.append({
                "group_id": doc.id,
                "group_name": data.get("group_name"),
                "category": data.get("category"),
                "current_member": data.get("current_member", 0),
                "max_member": data.get("max_member", 10),
                "description": data.get("description"),
                "group_image": data.get("group_image"),
            })

        return {
            "status": 200,
            "groups": groups
        }

    except Exception as e:
        print("[get_joined_groups]", e)
        raise HTTPException(status_code=500, detail="참여 소모임 조회 오류")