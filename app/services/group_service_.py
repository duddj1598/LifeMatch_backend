from typing import List, Optional, Dict, Any
from app.config.firebase_config import db
from app.schemas.group_schema import GroupCreate, GroupRead
from google.cloud import firestore
import uuid

COLLECTION = "groups"
DEFAULT_MAX_MEMBER = 10

def create_group(group: GroupCreate) -> Dict[str, Any]:
    payload = group.dict()
    if payload.get("max_member") is None:
        payload["max_member"] = DEFAULT_MAX_MEMBER
    payload = {k: v for k, v in payload.items() if v is not None}
    payload["created_at"] = firestore.SERVER_TIMESTAMP
    chat_id = str(uuid.uuid4())
    payload["chat_id"] = chat_id

    try:
        doc_ref = db.collection(COLLECTION).document()
        doc_ref.set(payload)
    except Exception as exc:
        return {
            "status": 500,
            "message": "그룹 생성 중 오류가 발생했습니다.",
            "error": str(exc)
        }

    return {
        "status": 201,
        "message": "그룹이 성공적으로 생성되었습니다.",
        "group_id": doc_ref.id,
        "chat_id": chat_id
    }

def _apply_client_side_defaults(data: Dict[str, Any]) -> Dict[str, Any]:
    if "max_member" not in data or data.get("max_member") is None:
        data["max_member"] = DEFAULT_MAX_MEMBER
    return data

def get_group_by_id(group_id: str) -> Optional[GroupRead]:
    try:
        doc = db.collection(COLLECTION).document(group_id).get()
        if not doc.exists:
            return None
        data = doc.to_dict()
        data = _apply_client_side_defaults(data)
        return GroupRead(id=doc.id, **data)
    except Exception:
        return None

def get_all_groups() -> List[GroupRead]:
    docs = db.collection(COLLECTION).stream()
    groups: List[GroupRead] = []
    for doc in docs:
        data = doc.to_dict()
        data = _apply_client_side_defaults(data)
        groups.append(GroupRead(id=doc.id, **data))
    return groups

def search_groups(
    group_name: Optional[str] = None,
    category: Optional[str] = None,
    min_member: Optional[int] = None,
    max_member: Optional[int] = None,
    created_after: Optional[firestore.SERVER_TIMESTAMP.__class__] = None,
    created_before: Optional[firestore.SERVER_TIMESTAMP.__class__] = None,
    sort_by: str = "created_at",
    desc: bool = True,
    limit: int = 50,
    offset: int = 0
) -> List[GroupRead]:
    """
    Firestore 쿼리 + 클라이언트 사이드 필터링을 결합한 검색 함수.
    - group_name: 부분 문자열 매칭(클라이언트 사이드)
    - category: 정확 매칭(서버 사이드 필터 우선 적용)
    - min_member/max_member: 서버에서 범위 필터가 가능하면 적용, 아니면 클라이언트 필터 적용
    - created_after/created_before: Firestore Timestamp 타입 사용 권장
    - sort_by: 인덱스 필요할 수 있음
    - limit/offset: offset은 stream 결과를 슬라이스로 처리
    """
    try:
        coll_ref = db.collection(COLLECTION)
        query = coll_ref

        # 서버 사이드에서 적용 가능한 필터 우선
        if category:
            query = query.where("category", "==", category)

        # Firestore는 range 쿼리와 복합 인덱스 제약이 있으므로 가능한 경우만 사용
        if min_member is not None:
            query = query.where("max_member", ">=", min_member)
        if max_member is not None:
            query = query.where("max_member", "<=", max_member)
        if created_after is not None:
            query = query.where("created_at", ">", created_after)
        if created_before is not None:
            query = query.where("created_at", "<", created_before)

        # 정렬 (정렬 필드는 인덱스 필요할 수 있음)
        direction = firestore.Query.DESCENDING if desc else firestore.Query.ASCENDING
        query = query.order_by(sort_by, direction=direction)

        # 스트리밍 후 추가 필터링(예: 부분일치)
        docs = list(query.stream())

        results: List[GroupRead] = []
        for doc in docs:
            data = doc.to_dict()
            data = _apply_client_side_defaults(data)

            # group_name 부분일치 필터링
            if group_name:
                if not isinstance(data.get("group_name"), str):
                    continue
                if group_name.lower() not in data["group_name"].lower():
                    continue

            # 만약 서버에서 range 처리 못한 경우 추가 검사
            if min_member is not None and data.get("max_member", DEFAULT_MAX_MEMBER) < min_member:
                continue
            if max_member is not None and data.get("max_member", DEFAULT_MAX_MEMBER) > max_member:
                continue

            results.append(GroupRead(id=doc.id, **data))

        # 페이징: offset + limit
        return results[offset: offset + limit]
    except Exception:
        return []
