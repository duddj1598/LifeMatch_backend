from typing import List, Optional, Dict, Any
import uuid
import ast

import numpy as np
from google.cloud import firestore

from app.config.firebase_config import db
from app.schemas.group_schema import GroupCreate, GroupRead

# 🔹 패널에서 쓰던 임베딩 모델 재활용
from app.config.llm_config import get_embedding_model

COLLECTION = "groups"
DEFAULT_MAX_MEMBER = 10


# -------------------------------------------------
# 공통 유틸
# -------------------------------------------------
def _apply_client_side_defaults(data: Dict[str, Any]) -> Dict[str, Any]:
    if "max_member" not in data or data.get("max_member") is None:
        data["max_member"] = DEFAULT_MAX_MEMBER
    return data


def _strip_timestamp(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Firestore의 created_at(Timestamp)을 응답에서 아예 제거.
    FastAPI 응답에서 Timestamp를 다루기 귀찮으면 이렇게 빼버리면 됨.
    """
    data = dict(data)  # 원본 훼손 방지
    data.pop("created_at", None)
    return data


def cosine_similarity(v1, v2) -> float:
    v1 = np.array(v1)
    v2 = np.array(v2)
    denom = np.linalg.norm(v1) * np.linalg.norm(v2)
    if denom == 0:
        return 0.0
    return float(np.dot(v1, v2) / denom)


# -------------------------------------------------
# 🔒 그룹 생성 (leader_id는 서버에서 세팅)
# -------------------------------------------------
def create_group(group: GroupCreate, leader_id: str) -> Dict[str, Any]:
    payload = group.dict()

    if payload.get("max_member") is None:
        payload["max_member"] = DEFAULT_MAX_MEMBER

    # 불필요한 None 제거
    payload = {k: v for k, v in payload.items() if v is not None}

    # Firestore에는 created_at을 Timestamp로 계속 저장 (정렬용 등)
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


## -------------------------------------------------
# 그룹 상세 조회
# -------------------------------------------------
def get_group_by_id(group_id: str) -> Optional[GroupRead]:
    try:
        doc = db.collection(COLLECTION).document(group_id).get()
        if not doc.exists:
            return None

        data = doc.to_dict()
        data = _apply_client_side_defaults(data)
        data = _strip_timestamp(data)

        # -----------------------------
        # 🔥 leader 정보 변환
        # -----------------------------
        leader_doc_id = data.get("leader_id")
        leader_login_id = None
        leader_nickname = None

        if leader_doc_id:
            leader_doc = db.collection("users").document(leader_doc_id).get()
            if leader_doc.exists:
                leader_data = leader_doc.to_dict()
                leader_login_id = leader_data.get("user_id")
                leader_nickname = leader_data.get("user_nickname")

        data["leader_nickname"] = leader_nickname
        data["leader_id"] = leader_login_id       
        data["current_member"] = data.get("current_member", 0)

        # -----------------------------
        # 🔥 멤버 목록 변환 (문서 ID → 닉네임)
        # -----------------------------
        member_doc_ids = data.get("members", [])
        members_nickname_list = []

        for user_doc_id in member_doc_ids:
            user_doc = db.collection("users").document(user_doc_id).get()
            if user_doc.exists:
                user_data = user_doc.to_dict()
                nickname = user_data.get("user_nickname")
                if nickname:
                    members_nickname_list.append(nickname)

        # GroupRead 스키마의 members 필드로 추가
        data["members"] = members_nickname_list  

        return GroupRead(id=doc.id, **data)

    except Exception as e:
        print(f"[get_group_by_id] error: {e}")
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
        data = _strip_timestamp(data)  # 🔥 created_at 제거
        groups.append(GroupRead(id=doc.id, **data))
    return groups


# -------------------------------------------------
# 🔥 의미 기반(임베딩) 검색 로직
# -------------------------------------------------
def apply_semantic_search(docs, query: str) -> List[GroupRead]:
    """
    - docs: Firestore DocumentSnapshot 리스트
    - query: 자연어 검색어
    - 각 문서에는 'embedding' 필드가 있다고 가정 (1차원 리스트 또는 문자열)
    """

    try:
        emb_model = get_embedding_model()
    except Exception as e:
        print(f"[apply_semantic_search] embedding model load failed: {e}")
        return []

    query_emb = emb_model.embed_query(query)
    scored = []

    for doc in docs:
        data = doc.to_dict()
        emb = data.get("embedding")

        if emb is None:
            continue

        # If embedding is a string (stored incorrectly)
        if isinstance(emb, str):
            try:
                emb = ast.literal_eval(emb)
            except Exception:
                continue

        # If embedding is list inside list
        if isinstance(emb, list) and len(emb) == 1 and isinstance(emb[0], list):
            emb = emb[0]

        # Ensure embedding is a 1D numeric list
        if not isinstance(emb, list):
            continue
        if not all(isinstance(x, (int, float)) for x in emb):
            continue

        # Compute similarity
        try:
            score = cosine_similarity(query_emb, emb)
        except Exception:
            continue

        data = _apply_client_side_defaults(data)
        data = _strip_timestamp(data)  # 🔥 created_at 제거

        scored.append({
            "doc_id": doc.id,
            "score": score,
            "data": data,
        })

    # Sort by score
    scored.sort(key=lambda x: x["score"], reverse=True)

    return [
        GroupRead(id=item["doc_id"], **item["data"])
        for item in scored
    ]


# -------------------------------------------------
# 🔍 그룹 검색 (자연어 + 카테고리만)
# -------------------------------------------------
def search_groups(
    query: Optional[str] = None,
    category: Optional[str] = None,
) -> List[GroupRead]:
    try:
        print("\n" * 2, "---------------------------------")
        print(f"[search_groups] query: {query}, category: {category}")

        coll_ref = db.collection(COLLECTION)
        q_ref = coll_ref

        # ------------------------------------------------
        # 1) 카테고리 필터
        # ------------------------------------------------
        if category:
            q_ref = q_ref.where("category", "==", category)
            print("[search_groups] category filter applied")

        docs = list(q_ref.stream())
        print(f"[search_groups] fetched docs: {len(docs)}")

        results: List[GroupRead] = []

        # ------------------------------------------------
        # 2) 검색어가 없으면 전체 반환
        # ------------------------------------------------
        if not query:
            print("[search_groups] no query → return all")
            for doc in docs:
                data = doc.to_dict()
                data = _apply_client_side_defaults(data)
                data = _strip_timestamp(data)
                results.append(GroupRead(id=doc.id, **data))
            return results

        # ------------------------------------------------
        # 3) 검색어가 있다면 이름/설명 부분 문자열 검색
        # ------------------------------------------------
        query_lower = query.lower()

        for doc in docs:
            data = doc.to_dict()
            name = str(data.get("group_name", "")).lower()
            desc = str(data.get("description", "")).lower()

            # 🔥 제목/설명 둘 중 하나라도 포함되면 통과
            if query_lower in name or query_lower in desc:
                data = _apply_client_side_defaults(data)
                data = _strip_timestamp(data)
                results.append(GroupRead(id=doc.id, **data))

        print(f"[search_groups] natural search results: {len(results)} groups")
        return results

    except Exception as e:
        print(f"[search_groups] error: {e}")
        return []



# -------------------------------------------------
# 🔥 그룹에 멤버 추가 (알림 수락 등에서 사용)
# -------------------------------------------------
def _add_member_to_group(group_id: str, user_id: str) -> bool:
    """
    notification_service 등에서 호출  
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
