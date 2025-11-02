from app.config.firebase_config import db
from app.schemas.group_schema import GroupCreate
from datetime import datetime

def create_group(group: GroupCreate):
    group_data = group.dict()
    group_data["created_at"] = datetime.utcnow()
    # Firestore에 새 문서 생성
    doc_ref = db.collection("groups").document()
    doc_ref.set(group_data)

    # 예시용으로 가상의 ID를 리턴 (실제 앱에서는 Firestore ID 사용 가능)
    return {
        "status": 200,
        "message": "그룹이 성공적으로 생성되었습니다.",
        "group_id": doc_ref.id,
        "chat_id": 1001  # 향후 채팅방 연동 시 동적으로 대체 가능
    }
