from app.config.firebase_config import db
from app.schemas.user_schema import UserCreate
from datetime import datetime, timedelta
from fastapi import HTTPException
import jwt  # PyJWT
import os

# 🔑 JWT 비밀키 (환경 변수로 관리 권장)
SECRET_KEY = os.getenv("JWT_SECRET", "your-secret-key")
ALGORITHM = "HS256"

def create_user(user: UserCreate):
    user_data = user.dict()
    user_data["created_at"] = datetime.utcnow()
    doc_ref = db.collection("users").document()
    doc_ref.set(user_data)
    return {"message": "회원가입 성공", "user_id": doc_ref.id}


def login_user(id: str, password: str):
    """
    유저 로그인 검증 (프론트에서 이미 암호화된 비밀번호를 보냄)
    """
    users_ref = db.collection("users")
    # id로 이메일 또는 닉네임 검색
    query_email = users_ref.where("user_email", "==", id).stream()
    query_nick = users_ref.where("user_nickname", "==", id).stream()

    found_user = None
    for doc in query_email:
        found_user = doc.to_dict()
        break
    if not found_user:
        for doc in query_nick:
            found_user = doc.to_dict()
            break

    if not found_user:
        raise HTTPException(status_code=404, detail="존재하지 않는 유저입니다.")

    # 🔒 프론트에서 이미 암호화된 비밀번호를 전송하므로 단순 비교
    if found_user["user_password"] != password:
        raise HTTPException(status_code=401, detail="비밀번호가 일치하지 않습니다.")

    # ✅ JWT 토큰 생성
    payload = {
        "sub": id,
        "exp": datetime.utcnow() + timedelta(hours=12),  # 12시간 유효
        "nickname": found_user.get("user_nickname"),
    }
    access_token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    return {
        "status": 200,
        "accessToken": access_token
    }
