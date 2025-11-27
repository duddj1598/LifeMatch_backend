from datetime import datetime
import uuid

from fastapi import HTTPException
from google.cloud import firestore

from app.config.firebase_config import db
from app.schemas.chat_schema import ChatMessageCreate, ChatRoomCreateRequest


def get_chat_list(user_id: str):
    chat_list = []

    # ===============================================
    # 🔥 1) 그룹 채팅 목록
    # ===============================================
    groups_ref = db.collection("groups").where(
        "members", "array_contains", user_id
    ).stream()

    for group_doc in groups_ref:
        data = group_doc.to_dict()
        chat_list.append({
            "chat_id": group_doc.id,
            "type": "group",
            "name": data.get("group_name", "모임 이름 없음"),
            "category": data.get("category", "기타"),
            "current_member": data.get("current_member", 0),
        })

    # ===============================================
    # 🔥 2) DM 채팅 목록 (상대방 닉네임 포함)
    # chat_rooms 컬렉션에서 type == "dm" AND members contains user
    # ===============================================
    dm_ref = db.collection("chat_rooms")\
        .where("type", "==", "dm")\
        .where("members", "array_contains", user_id)\
        .stream()

    for dm_doc in dm_ref:
        data = dm_doc.to_dict()
        members = data.get("members", [])

        # 🔥 본인 제외: 상대방 user_id
        other_user_id = [m for m in members if m != user_id]
        print(f"DM 상대방 ID 리스트: {other_user_id}")
        other_user_id = other_user_id[0] if other_user_id else None
        print(f"DM 상대방 ID: {other_user_id}")

        other_nickname = "알 수 없음"

        if other_user_id:
            # 🔥 Firestore에서 user_id == 로그인ID 로 문서 검색
            query = (
                db.collection("users")
                .where("user_id", "==", other_user_id)
                .limit(1)
                .stream()
            )

            other_user_doc = None
            for doc in query:
                other_user_doc = doc
                break

            if other_user_doc and other_user_doc.exists:
                user_data = other_user_doc.to_dict()
                other_nickname = user_data.get("user_nickname", "닉네임 없음")

        chat_list.append({
            "chat_id": dm_doc.id,
            "type": "dm",
            "name": other_nickname,        # 🔥 DM 상대방 닉네임 표시
            "members": members,
            "created_at": data.get("created_at"),
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

def _send_dm_message(chat_id: str, user_doc_id: str, payload: ChatMessageCreate):
    # 9자리 숫자 message_id
    message_id = int(str(uuid.uuid4().int)[:9])
    now = datetime.utcnow().isoformat() + "Z"

    message_data = {
        "message_id": message_id,
        "user_id": user_doc_id,
        "content": payload.content,
        "attachments": payload.attachments or [],
        "time": now,
    }

    # DM 메시지는 chat_rooms/{chat_id}/messages 에 저장
    db.collection("chat_rooms").document(chat_id) \
        .collection("messages").document(str(message_id)).set(message_data)

    return {
        "status": 200,
        "chat_id": chat_id,
        **message_data,
    }


# -------------------------------------------------
# 🔥 메시지 전송
# -------------------------------------------------
def send_message(chat_id: str, user_doc_id: str, payload: ChatMessageCreate):

    # 1) 그룹 채팅인지 확인
    group_ref = db.collection("groups").document(chat_id)
    group_doc = group_ref.get()

    if group_doc.exists:
        # 기존 그룹 메시지 처리 그대로 둠
        group_data = group_doc.to_dict()
        if user_doc_id not in group_data.get("members", []):
            raise HTTPException(status_code=403, detail="이 채팅방의 멤버가 아닙니다.")

        message_id = int(str(uuid.uuid4().int)[:9])
        now = datetime.utcnow().isoformat() + "Z"

        message_data = {
            "message_id": message_id,
            "user_id": user_doc_id,
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

    # 2) DM 채팅인지 확인
    dm_ref = db.collection("chat_rooms").document(chat_id)
    dm_doc = dm_ref.get()

    if dm_doc.exists:
        return _send_dm_message(chat_id, user_doc_id, payload)

    raise HTTPException(status_code=404, detail="채팅방을 찾을 수 없습니다.")

def _get_dm_chat_history(chat_id, user_doc_id, message_id, size):
    dm_ref = db.collection("chat_rooms").document(chat_id)
    dm_doc = dm_ref.get()

    if not dm_doc.exists:
        raise HTTPException(status_code=404, detail="채팅방을 찾을 수 없습니다.")

    messages_ref = dm_ref.collection("messages")

    if message_id is None:
        query = messages_ref.order_by(
            "message_id", direction=firestore.Query.DESCENDING
        ).limit(size)
    else:
        query = messages_ref.where("message_id", "<", int(message_id)) \
            .order_by("message_id", direction=firestore.Query.DESCENDING) \
            .limit(size)

    docs = list(query.stream())
    messages = []

    for doc in docs:
        msg = doc.to_dict()
        msg["is_mine"] = (msg.get("user_id") == user_doc_id)  # 🔥 추가
        messages.append(msg)

    next_msg = messages[-1]["message_id"] if len(messages) == size else None

    return {
        "messages": messages,
        "next_message_id": next_msg,
    }





# -------------------------------------------------
# 🔥 채팅 내역 조회 (위로 스크롤 페이징)
# -------------------------------------------------
def get_chat_history(chat_id: str, user_doc_id: str, message_id: int | None, size: int):

    # 1) 그룹 채팅인지
    group_ref = db.collection("groups").document(chat_id)
    group_doc = group_ref.get()

    if group_doc.exists:
        group_data = group_doc.to_dict()
        if user_doc_id not in group_data.get("members", []):
            raise HTTPException(status_code=403, detail="이 채팅방의 멤버가 아닙니다.")

        messages_ref = db.collection("groups").document(chat_id).collection("messages")

        if message_id is None:
            query = messages_ref.order_by("message_id", direction=firestore.Query.DESCENDING).limit(size)
        else:
            query = messages_ref.where("message_id", "<", int(message_id)) \
                .order_by("message_id", direction=firestore.Query.DESCENDING).limit(size)

        docs = list(query.stream())
        messages = []

        for doc in docs:
            msg = doc.to_dict()
            msg["is_mine"] = (msg.get("user_id") == user_doc_id)   # 🔥 추가
            print(f"메시지: {msg}")
            messages.append(msg)

        next_msg = messages[-1]["message_id"] if len(messages) == size else None

        return {
            "messages": messages,
            "next_message_id": next_msg
        }

    # 2) DM 채팅이면 여기로
    return _get_dm_chat_history(chat_id, user_doc_id, message_id, size)



def _generate_dm_key(u1: str, u2: str) -> str:
    """DM 고유 키: user_id 두 개를 정렬해서 묶음"""
    return "|".join(sorted([u1, u2]))


def create_chat_room(req: ChatRoomCreateRequest, current_user_id: str):
    """
    채팅방 생성:
    - type == "group": 이미 존재하는 그룹 채팅 정보 반환
    - type == "dm": 나(current_user) + 상대(target_ids[0]) DM 생성 (또는 기존 것 반환)
    """

    chat_type = req.type

    # 🔹 JWT에서 현재 유저 ID 가져오기 (user_id 우선, 없으면 user_doc_id 사용)
    if not current_user_id:
        raise HTTPException(status_code=500, detail="현재 사용자 ID를 찾을 수 없습니다.")
    print(f"현재 사용자 ID: {current_user_id}") 

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
        # DM은 target_ids에 상대 user_id 1개만 포함
        if not req.target_ids or len(req.target_ids) != 1:
            raise HTTPException(
                status_code=400,
                detail="DM 생성 시 target_ids에는 상대 user_id 1개만 포함해야 합니다.",
            )

        target_login_id = req.target_ids[0]

        # ============================================
        # 🔥 1) target_login_id → Firestore 문서 조회
        # ============================================
        query = db.collection("users").where("user_id", "==", target_login_id).limit(1).stream()

        if not target_login_id:
            raise HTTPException(status_code=404, detail="해당 유저를 찾을 수 없습니다.")

        target_doc_id = target_login_id

        # ============================================
        # 🔥 2) 자기 자신 DM 생성 방지 (user_id 기준)
        # ============================================
        if target_doc_id == current_user_id:
            raise HTTPException(status_code=400, detail="자기 자신과 DM은 생성할 수 없습니다.")

        # ============================================
        # 🔥 3) DM 키 생성 (문서 ID 기준)
        # ============================================
        current_doc_id = current_user_id
        dm_key = _generate_dm_key(current_doc_id, target_doc_id)

        # 기존 DM 존재 확인
        existing_doc = db.collection("chat_rooms").document(dm_key).get()
        if existing_doc.exists:
            data = existing_doc.to_dict()
            return {
                "status": 200,
                "chat_id": data["chat_id"],
                "members": data["members"],
                "message": "이미 존재하는 DM 채팅방을 반환합니다.",
            }

        # 새 방 생성
        new_room = {
            "chat_id": dm_key,
            "type": "dm",
            "dm_key": dm_key,
            "members": [current_doc_id, target_doc_id],
            "created_at": datetime.utcnow(),
        }
        db.collection("chat_rooms").document(dm_key).set(new_room)

        return {
            "status": 201,
            "chat_id": dm_key,
            "members": [current_doc_id, target_doc_id],
            "message": "새로운 DM 채팅방이 생성되었습니다.",
        }


    # ============================================
    # 🔥 잘못된 type 처리
    # ============================================
    else:
        raise HTTPException(status_code=400, detail="type은 group 또는 dm 이어야 합니다.")
