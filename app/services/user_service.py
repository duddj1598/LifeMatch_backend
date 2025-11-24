from app.config.firebase_config import db
from app.schemas.user_schema import UserCreate
from datetime import datetime, timedelta
from fastapi import HTTPException
import jwt
import os

SECRET_KEY = os.getenv("JWT_SECRET", "your-secret-key")
ALGORITHM = "HS256"



def create_user(user: UserCreate):
    user_data = user.dict()
    user_data["created_at"] = datetime.utcnow()

    user_ref = db.collection("users").document()
    user_ref.set(user_data)

    return {
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
    print("🔍 [find_user_id] 들어온 값:")
    print(f" email = {email}")
    print(f" question = {question}")
    print(f" answer = {answer}")

    users_ref = db.collection("users")
    query = users_ref.where("user_email", "==", email).limit(1).stream()

    found_doc = None
    found_user = None

    for doc in query:
        found_doc = doc
        found_user = doc.to_dict()
        break

    print(f"🔥 [find_user_id] Firestore에서 조회된 사용자: {found_user}")

    # 이메일 존재 확인
    if not found_user:
        print("❌ [ERROR] 이메일 없음")
        raise HTTPException(status_code=404, detail="존재하지 않는 이메일입니다.")

    # 보안질문 & 답변 존재 여부 확인
    user_q = found_user.get("user_security_question")
    user_a = found_user.get("user_security_answer")

    print(f"🔥 DB 저장된 question = {user_q}")
    print(f"🔥 DB 저장된 answer   = {user_a}")

    if user_q is None or user_a is None:
        print("❌ [ERROR] DB에 question 또는 answer 필드 없음")
        raise HTTPException(status_code=500, detail="서버 데이터 오류: 보안질문 또는 답변이 없습니다.")

    # 비교
    if user_q != question or user_a != answer:
        print("❌ [ERROR] 질문 또는 답변 불일치")
        print(f"사용자 입력 Q = {question}, DB Q = {user_q}")
        print(f"사용자 입력 A = {answer}, DB A = {user_a}")
        raise HTTPException(status_code=401, detail="본인 확인 정보가 일치하지 않습니다.")

    print("✅ [SUCCESS] user_id 반환:", found_user.get("user_id"))
    return found_user.get("user_id")

def reset_password(login_id: str, email: str, question: str, answer: str, new_password: str):
    users_ref = db.collection("users")

    query_email = users_ref.where("user_email", "==", login_id).stream()
    query_nick = users_ref.where("user_nickname", "==", login_id).stream()

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
