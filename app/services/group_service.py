from app.config.firebase_config import db
from app.schemas.group_schema import GroupCreate
from datetime import datetime

def create_group(group: GroupCreate):
    group_data = group.dict()
    group_data["created_at"] = datetime.utcnow()
    doc_ref = db.collection("groups").document()
    doc_ref.set(group_data)

    return {
        "status": 200,
        "message": "그룹이 성공적으로 생성되었습니다.",
        "group_id": doc_ref.id,
        "chat_id": 1001
    }
