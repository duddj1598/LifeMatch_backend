from datetime import datetime
import uuid

from fastapi import HTTPException
from google.cloud import firestore

from app.config.firebase_config import db
from app.schemas.chat_schema import ChatMessageCreate, ChatRoomCreateRequest


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

def _generate_dm_key(u1: str, u2: str) -> str:
    """DM 고유 키: user_id 두 개를 정렬해서 묶음"""
    return "|".join(sorted([u1, u2]))


def create_chat_room(req: ChatRoomCreateRequest, current_user: dict):
    """
    채팅방 생성:
    - type == "group": 이미 존재하는 그룹 채팅 정보 반환
    - type == "dm": 나(current_user) + 상대(target_ids[0]) DM 생성 (또는 기존 것 반환)
    """

    chat_type = req.type

    # 🔹 JWT에서 현재 유저 ID 가져오기 (user_id 우선, 없으면 user_doc_id 사용)
    current_user_id = current_user.get("user_id") or current_user.get("user_doc_id")
    if not current_user_id:
        raise HTTPException(status_code=500, detail="현재 사용자 ID를 찾을 수 없습니다.")

    # ============================================
    # 🔥 1) 그룹 채팅 (group)
    # ============================================
    if chat_type == "group":
        if not req.group_id:
            raise HTTPException(status_code=400, detail="group_id가 필요합니다.")

        group_ref = db.collection("groups").document(req.group_id)
        group_doc = group_ref.get()

        if not group_doc.exists:
            raise HTTPException(status_code=404, detail="그룹이 존재하지 않습니다.")

        group_data = group_doc.to_dict()
        members = group_data.get("members", [])

        # 그룹 채팅은 이미 groups 컬렉션 기준으로 존재한다고 보고,
        # 그냥 정보만 반환
        return {
            "status": 200,
            "chat_id": req.group_id,   # 그룹 채팅은 group_id = chat_id
            "members": members,
            "message": "그룹 채팅방 정보입니다.",
        }

    # ============================================
    # 🔥 2) DM 채팅 (dm)
    # ============================================
    elif chat_type == "dm":
        # DM은 프론트에서 target_ids에 "상대 user_id" 1개만 보내도록 설계
        if not req.target_ids or len(req.target_ids) != 1:
            raise HTTPException(
                status_code=400,
                detail="DM 생성 시 target_ids에는 상대 user_id 1개만 포함해야 합니다.",
            )

        target_user_id = req.target_ids[0]

        if target_user_id == current_user_id:
            raise HTTPException(status_code=400, detail="자기 자신과 DM은 생성할 수 없습니다.")

        # 🔑 user_id 2개로 dm_key 생성
        dm_key = _generate_dm_key(current_user_id, target_user_id)

        # 이미 존재하는 DM 채팅방 있는지 확인
        existing_doc = db.collection("chat_rooms").document(dm_key).get()
        if existing_doc.exists:
            data = existing_doc.to_dict()
            return {
                "status": 200,
                "chat_id": data["chat_id"],
                "members": data["members"],
                "message": "이미 존재하는 DM 채팅방을 반환합니다.",
            }

        # 없으면 새로 생성
        new_room = {
            "chat_id": dm_key,
            "type": "dm",
            "dm_key": dm_key,
            "members": [current_user_id, target_user_id],  # 🔥 user_id 기준
            "created_at": datetime.utcnow(),
        }
        db.collection("chat_rooms").document(dm_key).set(new_room)

        return {
            "status": 201,
            "chat_id": dm_key,
            "members": [current_user_id, target_user_id],
            "message": "새로운 DM 채팅방이 생성되었습니다.",
        }

    # ============================================
    # 🔥 잘못된 type 처리
    # ============================================
    else:
        raise HTTPException(status_code=400, detail="type은 group 또는 dm 이어야 합니다.")
