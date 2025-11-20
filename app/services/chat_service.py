from app.config.firebase_config import db
from app.schemas.chat_schema import ChatMessageCreate
from datetime import datetime
from fastapi import HTTPException
import uuid


def _get_user_id_from_email(user_email: str) -> str:
    """이메일로 사용자 문서 ID 조회"""
    users_ref = db.collection("users")
    query = users_ref.where("user_email", "==", user_email).limit(1).stream()
    
    for doc in query:
        return doc.id
    
    raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")


def get_chat_list(user_email: str):
    """유저의 소모임 채팅방 목록 조회"""
    user_id = _get_user_id_from_email(user_email)
    
    # 사용자가 속한 그룹 찾기
    groups_ref = db.collection("groups").where("members", "array_contains", user_id).stream()
    
    chat_list = []
    for group_doc in groups_ref:
        group_data = group_doc.to_dict()
        chat_list.append({
            "group_name": group_data.get("group_name", "모임 이름 없음"),
            "category": group_data.get("category", "기타"),
            "current_member": group_data.get("current_member", 0)
        })
    
    return {
        "status": 200,
        "list": chat_list
    }


def leave_chat_room(chat_id: str, user_email: str):
    """유저가 속한 소모임 채팅방에서 퇴장"""
    user_id = _get_user_id_from_email(user_email)
    
    # chat_id는 실제로 group_id
    group_ref = db.collection("groups").document(chat_id)
    group_doc = group_ref.get()
    
    if not group_doc.exists:
        raise HTTPException(status_code=404, detail="채팅방을 찾을 수 없습니다.")
    
    group_data = group_doc.to_dict()
    members = group_data.get("members", [])
    
    if user_id not in members:
        raise HTTPException(status_code=400, detail="이 채팅방의 멤버가 아닙니다.")
    
    # 멤버에서 제거
    from google.cloud import firestore
    group_ref.update({
        "members": firestore.ArrayRemove([user_id]),
        "current_member": firestore.Increment(-1)
    })
    
    return {"status": 200}


def send_message(chat_id: str, user_email: str, payload: ChatMessageCreate):
    """채팅방에 메시지 전송"""
    user_id = _get_user_id_from_email(user_email)
    
    # chat_id는 실제로 group_id
    group_ref = db.collection("groups").document(chat_id)
    group_doc = group_ref.get()
    
    if not group_doc.exists:
        raise HTTPException(status_code=404, detail="채팅방을 찾을 수 없습니다.")
    
    group_data = group_doc.to_dict()
    if user_id not in group_data.get("members", []):
        raise HTTPException(status_code=403, detail="이 채팅방의 멤버가 아닙니다.")
    
    # 메시지 ID 생성
    message_id = int(str(uuid.uuid4().int)[:9])  # 9자리 숫자
    current_time = datetime.utcnow().isoformat() + "Z"
    
    # 메시지 데이터
    message_data = {
        "message_id": message_id,
        "user_id": int(user_id) if user_id.isdigit() else hash(user_id) % (10**9),
        "content": payload.content,
        "attachments": payload.attachments or [],
        "time": current_time
    }
    
    # Firestore에 저장 (groups/{group_id}/messages 서브컬렉션)
    db.collection("groups").document(chat_id)\
        .collection("messages").document(str(message_id)).set(message_data)
    
    return {
        "status": 200,
        "message_id": message_id,
        "chat_id": chat_id,
        "user_id": message_data["user_id"],
        "content": payload.content,
        "attachments": message_data["attachments"],
        "time": current_time
    }


def get_chat_history(chat_id: str, user_email: str, message_id: str, size: int):
    """채팅방 참여자의 채팅 내역 불러오기"""
    user_id = _get_user_id_from_email(user_email)
    
    # chat_id는 실제로 group_id
    group_ref = db.collection("groups").document(chat_id)
    group_doc = group_ref.get()
    
    if not group_doc.exists:
        raise HTTPException(status_code=404, detail="채팅방을 찾을 수 없습니다.")
    
    group_data = group_doc.to_dict()
    if user_id not in group_data.get("members", []):
        raise HTTPException(status_code=403, detail="이 채팅방의 멤버가 아닙니다.")
    
    # 메시지 조회
    messages_ref = db.collection("groups").document(chat_id).collection("messages")
    
    if message_id:
        # 특정 메시지 이후 조회 (페이징)
        query = messages_ref.order_by("time").start_after({"message_id": int(message_id)}).limit(size)
    else:
        # 최신 메시지부터 조회
        query = messages_ref.order_by("time", direction="DESCENDING").limit(size)
    
    messages = []
    for doc in query.stream():
        data = doc.to_dict()
        messages.append({
            "message_id": data.get("message_id"),
            "user_id": data.get("user_id"),
            "content": data.get("content"),
            "attachments": data.get("attachments", []),
            "time": data.get("time")
        })
    
    # 다음 페이지 ID
    next_message_id = messages[-1]["message_id"] if len(messages) == size else None
    
    return {
        "messages": messages,
        "next_message_id": next_message_id
    }