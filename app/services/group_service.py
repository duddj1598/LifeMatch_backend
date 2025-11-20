from typing import List, Optional, Dict, Any
from app.config.firebase_config import db
from app.schemas.group_schema import GroupCreate, GroupRead
from google.cloud import firestore
import uuid

COLLECTION = "groups"
DEFAULT_MAX_MEMBER = 10

# 그룹 데이터에 max_member 값이 없을 때 기본값(10)을 자동으로 채워주는 역할
def _apply_client_side_defaults(data: Dict[str, Any]) -> Dict[str, Any]:
    if "max_member" not in data or data.get("max_member") is None:
        data["max_member"] = DEFAULT_MAX_MEMBER
    return data

def create_group(group: GroupCreate) -> Dict[str, Any]:
    payload = group.dict()  # GroupCreate 객체를 딕셔너리로 변환
    if payload.get("max_member") is None:  # max_member 값이 없으면
        payload["max_member"] = DEFAULT_MAX_MEMBER  # 기본값(10)으로 설정
    payload = {k: v for k, v in payload.items() if v is not None}  # 값이 None인 항목은 제거
    payload["created_at"] = firestore.SERVER_TIMESTAMP  # 생성 시각을 Firestore 서버 타임스탬프로 저장
    chat_id = str(uuid.uuid4())  # 고유한 chat_id 생성
    payload["chat_id"] = chat_id  # chat_id 필드에 추가

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

# 그룹 ID로 그룹 상세 정보 조회
def get_group_by_id(group_id: str) -> Optional[GroupRead]:
    try:
        doc = db.collection(COLLECTION).document(group_id).get()  # 해당 group_id의 문서 조회
        if not doc.exists:  # 문서가 존재하지 않으면
            return None  # None 반환
        data = doc.to_dict()  # 문서 데이터를 딕셔너리로 변환
        data = _apply_client_side_defaults(data)  # max_member 등 기본값 보정
        
        if isinstance(data.get("created_at"), firestore.Timestamp):  # created_at이 Firestore Timestamp면
            data["created_at"] = data["created_at"].to_datetime().isoformat()  # ISO 포맷 문자열로 변환
        return GroupRead(id=doc.id, **data)  # GroupRead 객체로 반환
    except Exception:
        return None

# 모든 그룹 목록 조회
def get_all_groups() -> List[GroupRead]:
    docs = db.collection(COLLECTION).stream()  # 모든 그룹 문서 스트림으로 가져오기
    groups: List[GroupRead] = []  # 결과를 담을 리스트
    for doc in docs:
        data = doc.to_dict()  # 문서 데이터를 딕셔너리로 변환
        data = _apply_client_side_defaults(data)  # max_member 등 기본값 보정
        if isinstance(data.get("created_at"), firestore.Timestamp):  # created_at이 Firestore Timestamp면
            data["created_at"] = data["created_at"].to_datetime().isoformat()  # ISO 포맷 문자열로 변환
        groups.append(GroupRead(id=doc.id, **data))  # GroupRead 객체로 변환해 리스트에 추가
    return groups  # 전체 그룹 리스트 반환

# 그룹 검색 기능 구현
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
    offset: int = 0
) -> List[GroupRead]:
    try:
        coll_ref = db.collection(COLLECTION)  # 그룹 컬렉션 참조
        query = coll_ref  # 쿼리 객체 초기화

        if category:  # 카테고리로 필터링
            query = query.where("category", "==", category)
        if min_member is not None:  # 최소 멤버 수로 필터링
            query = query.where("max_member", ">=", min_member)
        if max_member is not None:  # 최대 멤버 수로 필터링
            query = query.where("max_member", "<=", max_member)
        if created_after is not None:  # 생성일 이후로 필터링
            query = query.where("created_at", ">", created_after)
        if created_before is not None:  # 생성일 이전으로 필터링
            query = query.where("created_at", "<", created_before)

        direction = firestore.Query.DESCENDING if desc else firestore.Query.ASCENDING  # 정렬 방향 결정
        query = query.order_by(sort_by, direction=direction)  # 정렬 필드 및 방향 적용

        docs = list(query.stream())  # 쿼리 결과 문서 리스트로 변환
        results: List[GroupRead] = []  # 결과를 담을 리스트
        for doc in docs:
            data = doc.to_dict()  # 문서 데이터를 딕셔너리로 변환
            data = _apply_client_side_defaults(data)  # max_member 등 기본값 보정

            if group_name:  # 그룹명 부분 검색
                if not isinstance(data.get("group_name"), str):
                    continue  # group_name이 문자열이 아니면 건너뜀
                if group_name.lower() not in data["group_name"].lower():
                    continue  # 부분 문자열이 아니면 건너뜀

            # 멤버 수 조건 재확인(파이어스토어 쿼리 한계 보완)
            if min_member is not None and data.get("max_member", DEFAULT_MAX_MEMBER) < min_member:
                continue
            if max_member is not None and data.get("max_member", DEFAULT_MAX_MEMBER) > max_member:
                continue

            if isinstance(data.get("created_at"), firestore.Timestamp):  # created_at이 Firestore Timestamp면
                data["created_at"] = data["created_at"].to_datetime().isoformat()  # ISO 포맷 문자열로 변환

            results.append(GroupRead(id=doc.id, **data))  # GroupRead 객체로 변환해 리스트에 추가

        return results[offset: offset + limit]  # 오프셋과 limit 적용해 결과 반환
    except Exception:
        return []  # 예외 발생 시 빈 리스트 반환
def _add_member_to_group(group_id: str, user_id: str) -> bool:
    """
    그룹에 사용자를 멤버로 추가합니다.
    """
    try:
        group_ref = db.collection(COLLECTION).document(group_id)
        
        # 멤버 배열에 user_id를 추가하는 Atomic Update (배열 요소 추가)
        group_ref.update({
            "members": firestore.ArrayUnion([user_id]),
            "current_member": firestore.Increment(1)  # 현재 멤버 수 1 증가
        })
        
        return True
    except Exception as e:
        print(f"Error adding member to group {group_id}: {e}")
        return False