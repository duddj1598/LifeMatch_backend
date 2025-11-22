from typing import List, Optional, Dict, Any
import uuid

from google.cloud import firestore

from app.config.firebase_config import db
from app.schemas.group_schema import GroupCreate, GroupRead

COLLECTION = "groups"
DEFAULT_MAX_MEMBER = 10


def _apply_client_side_defaults(data: Dict[str, Any]) -> Dict[str, Any]:
    if "max_member" not in data or data.get("max_member") is None:
        data["max_member"] = DEFAULT_MAX_MEMBER
    return data


# -------------------------------------------------
# 🔒 그룹 생성 (leader_id는 서버에서 세팅)
# -------------------------------------------------
def create_group(group: GroupCreate, leader_id: str) -> Dict[str, Any]:
    # 프론트에서 넘어온 leader_id는 무시하고 서버 기준으로 덮어씀
    payload = group.dict(exclude={"leader_id"})

    if payload.get("max_member") is None:
        payload["max_member"] = DEFAULT_MAX_MEMBER

    payload = {k: v for k, v in payload.items() if v is not None}

    payload["created_at"] = firestore.SERVER_TIMESTAMP
    chat_id = str(uuid.uuid4())
    payload["chat_id"] = chat_id

    # 리더/멤버 정보 초기화
    payload["leader_id"] = leader_id
    payload["members"] = [leader_id]
    payload["current_member"] = 1

    try:
        doc_ref = db.collection(COLLECTION).document()
        doc_ref.set(payload)
    except Exception as exc:
        return {
            "status": 500,
            "message": "그룹 생성 중 오류가 발생했습니다.",
            "error": str(exc),
        }

    return {
        "status": 201,
        "message": "그룹이 성공적으로 생성되었습니다.",
        "group_id": doc_ref.id,
        "chat_id": chat_id,
    }


# -------------------------------------------------
# 그룹 상세 조회
# -------------------------------------------------
def get_group_by_id(group_id: str) -> Optional[GroupRead]:
    try:
        doc = db.collection(COLLECTION).document(group_id).get()
        if not doc.exists:
            return None

        data = doc.to_dict()
        data = _apply_client_side_defaults(data)

        if isinstance(data.get("created_at"), firestore.Timestamp):
            data["created_at"] = data["created_at"].to_datetime().isoformat()

        return GroupRead(id=doc.id, **data)
    except Exception:
        return None


# -------------------------------------------------
# 전체 그룹 목록 (내부용)
# -------------------------------------------------
def get_all_groups() -> List[GroupRead]:
    docs = db.collection(COLLECTION).stream()
    groups: List[GroupRead] = []
    for doc in docs:
        data = doc.to_dict()
        data = _apply_client_side_defaults(data)
        if isinstance(data.get("created_at"), firestore.Timestamp):
            data["created_at"] = data["created_at"].to_datetime().isoformat()
        groups.append(GroupRead(id=doc.id, **data))
    return groups


# -------------------------------------------------
# 그룹 검색
# -------------------------------------------------
def search_groups(
    group_name: Optional[str] = None,
    category: Optional[str] = None,
    min_member: Optional[int] = None,
    max_member: Optional[int] = None,
    created_after: Optional[Any] = None,
    created_before: Optional[Any] = None,
    sort_by: str = "created_at",
    desc: bool = True,
    limit: int = 50,
    offset: int = 0,
) -> List[GroupRead]:
    try:
        coll_ref = db.collection(COLLECTION)
        query = coll_ref

        if category:
            query = query.where("category", "==", category)
        if min_member is not None:
            query = query.where("max_member", ">=", min_member)
        if max_member is not None:
            query = query.where("max_member", "<=", max_member)
        if created_after is not None:
            query = query.where("created_at", ">", created_after)
        if created_before is not None:
            query = query.where("created_at", "<", created_before)

        direction = firestore.Query.DESCENDING if desc else firestore.Query.ASCENDING
        query = query.order_by(sort_by, direction=direction)

        docs = list(query.stream())
        results: List[GroupRead] = []

        for doc in docs:
            data = doc.to_dict()
            data = _apply_client_side_defaults(data)

            if group_name:
                if not isinstance(data.get("group_name"), str):
                    continue
                if group_name.lower() not in data["group_name"].lower():
                    continue

            if min_member is not None and data.get("max_member", DEFAULT_MAX_MEMBER) < min_member:
                continue
            if max_member is not None and data.get("max_member", DEFAULT_MAX_MEMBER) > max_member:
                continue

            if isinstance(data.get("created_at"), firestore.Timestamp):
                data["created_at"] = data["created_at"].to_datetime().isoformat()

            results.append(GroupRead(id=doc.id, **data))

        return results[offset: offset + limit]
    except Exception:
        return []


# -------------------------------------------------
# 🔥 그룹에 멤버 추가 (알림 수락 등에서 사용)
# -------------------------------------------------
def _add_member_to_group(group_id: str, user_id: str) -> bool:
    """
    group_actions → notification_service 에서 호출  
    user_id는 Firestore users 문서 ID
    """
    try:
        group_ref = db.collection(COLLECTION).document(group_id)
        group_ref.update({
            "members": firestore.ArrayUnion([user_id]),
            "current_member": firestore.Increment(1),
        })
        return True
    except Exception as e:
        print(f"Error adding member to group {group_id}: {e}")
        return False
