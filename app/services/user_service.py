from app.config.firebase_config import db
from app.schemas.user_schema import UserCreate
from datetime import datetime

def create_user(user: UserCreate):
    user_data = user.dict()
    user_data["created_at"] = datetime.utcnow()
    doc_ref = db.collection("users").document()
    doc_ref.set(user_data)
    return {"message": "회원가입 성공", "user_id": doc_ref.id}
