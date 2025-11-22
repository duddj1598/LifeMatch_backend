from datetime import datetime
import uuid

from fastapi import HTTPException
from google.cloud import firestore

from app.config.firebase_config import db
from app.schemas.chat_schema import ChatMessageCreate


# -------------------------------------------------
# 🔥 채팅방 목록 조회
# -------------------------------------------------
def get_chat_list(user_doc_id: str):
    """
    Firestore:
    - groups 컬렉션에서 members 배열에 user_doc_id가 포함된 문서들 조회
    """
    groups_ref = db.collection("groups").where(
        "members", "array_contains", user_doc_id
    ).stream()

    chat_list = []
    for group_doc in groups_ref:
        group_data = group_doc.to_dict()
        chat_list.append({
            "chat_id": group_doc.id,  # 프론트에서 이걸 chat_id로 사용하면 됨
            "group_name": group_data.get("group_name", "모임 이름 없음"),
            "category": group_data.get("category", "기타"),
            "current_member": group_data.get("current_member", 0),
        })

    return {
        "status": 200,
        "list": chat_list,
    }


# -------------------------------------------------
# 🔥 채팅방 퇴장
# -------------------------------------------------
def leave_chat_room(chat_id: str, user_doc_id: str):
    group_ref = db.collection("groups").document(chat_id)
    group_doc = group_ref.get()

    if not group_doc.exists:
        raise HTTPException(status_code=404, detail="채팅방을 찾을 수 없습니다.")

    group_data = group_doc.to_dict()
    members = group_data.get("members", [])

    if user_doc_id not in members:
        raise HTTPException(status_code=403, detail="이 채팅방의 멤버가 아닙니다.")

    group_ref.update({
        "members": firestore.ArrayRemove([user_doc_id]),
        "current_member": firestore.Increment(-1),
    })

    return {"status": 200, "message": "채팅방에서 퇴장했습니다."}


# -------------------------------------------------
# 🔥 메시지 전송
# -------------------------------------------------
def send_message(chat_id: str, user_doc_id: str, payload: ChatMessageCreate):
    group_ref = db.collection("groups").document(chat_id)
    group_doc = group_ref.get()

    if not group_doc.exists:
        raise HTTPException(status_code=404, detail="채팅방을 찾을 수 없습니다.")

    group_data = group_doc.to_dict()
    if user_doc_id not in group_data.get("members", []):
        raise HTTPException(status_code=403, detail="이 채팅방의 멤버가 아닙니다.")

    # 9자리 숫자 message_id
    message_id = int(str(uuid.uuid4().int)[:9])
    now = datetime.utcnow().isoformat() + "Z"

    message_data = {
        "message_id": message_id,
        "user_id": user_doc_id,  # 🔥 이제 Firestore user_doc_id 그대로 저장
        "content": payload.content,
        "attachments": payload.attachments or [],
        "time": now,
    }

    db.collection("groups").document(chat_id) \
        .collection("messages").document(str(message_id)).set(message_data)

    return {
        "status": 200,
        "chat_id": chat_id,
        **message_data,
    }


# -------------------------------------------------
# 🔥 채팅 내역 조회 (위로 스크롤 페이징)
# -------------------------------------------------
def get_chat_history(
    chat_id: str,
    user_doc_id: str,
    message_id: int | None,
    size: int,
):
    group_ref = db.collection("groups").document(chat_id)
    group_doc = group_ref.get()

    if not group_doc.exists:
        raise HTTPException(status_code=404, detail="채팅방을 찾을 수 없습니다.")

    group_data = group_doc.to_dict()
    if user_doc_id not in group_data.get("members", []):
        raise HTTPException(status_code=403, detail="이 채팅방의 멤버가 아닙니다.")

    messages_ref = db.collection("groups").document(chat_id).collection("messages")

    # 최신부터 N개
    if message_id is None:
        query = messages_ref.order_by(
            "message_id", direction=firestore.Query.DESCENDING
        ).limit(size)
    else:
        # 더 이전 메시지 N개 (message_id보다 작은 것들)
        query = (
            messages_ref.where("message_id", "<", int(message_id))
            .order_by("message_id", direction=firestore.Query.DESCENDING)
            .limit(size)
        )

    docs = list(query.stream())
    messages = [doc.to_dict() for doc in docs]

    next_message_id = messages[-1]["message_id"] if len(messages) == size else None

    # 프론트는 messages 배열을 시간 순으로 쓰고 싶다면 역순 정렬하면 됨
    return {
        "messages": messages,
        "next_message_id": next_message_id,
    }
