from app.config.firebase_config import db
from app.schemas.group_schema import GroupCreate, GroupUpdate
from datetime import datetime
from fastapi import HTTPException
from google.cloud import firestore

def create_group(group: GroupCreate):
    group_data = group.dict()
    group_data["created_at"] = datetime.utcnow()
    # [수정] 멤버/리더 정보 초기화
    leader_id = group_data.get("leader_id")
    group_data["members"] = [leader_id] if leader_id else []
    group_data["current_member"] = 1 if leader_id else 0
    
    doc_ref = db.collection("groups").document()
    doc_ref.set(group_data)
    return {"status": 200, "message": "그룹 생성 성공", "group_id": doc_ref.id}

def update_group(group_id: str, group: GroupUpdate):
    doc_ref = db.collection("groups").document(group_id)
    if not doc_ref.get().exists:
        raise HTTPException(status_code=404, detail="그룹을 찾을 수 없습니다.")
    doc_ref.update(group.dict(exclude_unset=True))
    return {"status": 200, "message": "그룹 정보 수정 완료"}

def get_group_list(category: str, page: int, size: int):
    query = db.collection("groups")
    if category:
        query = query.where("category", "==", category)
    groups = query.stream()
    group_list = []
    for g in groups:
        data = g.to_dict()
        group_list.append({
            "group_name": data.get("group_name"),
            "category": data.get("category"),
            "max_member": data.get("max_member"),
            "current_member": data.get("current_member"),
        })
    start = (page - 1) * size
    end = start + size
    return {"status": 200, "list": group_list[start:end]}


'''
(기존 코드에서 수정 있음)
기존 get_group_detail 함수는 groups 컬렉션만 조회해서 leader_id (팀장의 ID)만 반환할 뿐, 그 ID를 이용해 users 컬렉션에서 팀장의 닉네임이나 관심사를 가져오지 않음
따라서, leader_id를 가져온 뒤, db.collection("users").document(leader_id).get()을 한 번 더 호출해서 팀장의 닉네임과 라이프스타일 유형(관심사)을 함께 조회하여 반환하도록 수정함
'''
def get_group_detail(group_id: str):
    doc = db.collection("groups").document(group_id).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="존재하지 않는 그룹입니다.")
    
    data = doc.to_dict()
    
    leader_id = data.get("leader_id")
    leader_nickname = "알 수 없음"
    leader_interest = "알 수 없음"

    if leader_id:
        leader_doc = db.collection("users").document(leader_id).get()
        if leader_doc.exists:
            leader_data = leader_doc.to_dict()
            leader_nickname = leader_data.get("user_nickname", "닉네임 없음")
            leader_interest = leader_data.get("user_lifestyle_type", "유형 없음") 
    
    return {
        "status": 200,
        "group_name": data.get("group_name"),
        "category": data.get("category"),
        "max_member": data.get("max_member"),
        "current_member": data.get("current_member"),
        "description": data.get("description"),
        "leader_nickname": leader_nickname,
        "leader_interest": leader_interest,
        "group_image": data.get("group_image"),
        "leader_id": leader_id
    }

def get_group_members(group_id: str):
    doc = db.collection("groups").document(group_id).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="그룹을 찾을 수 없습니다.")
    members = doc.to_dict().get("members", [])
    member_data = []
    for uid in members:
        user_doc = db.collection("users").document(uid).get()
        if user_doc.exists:
            u = user_doc.to_dict()
            member_data.append({
                "user_id": uid,
                "nickname": u.get("user_nickname"),
                "profile_image": u.get("profile_image")
            })
    return {"status": 200, "member": member_data}

def get_my_groups(user_id: str):
    groups_ref = db.collection("groups").where("members", "array_contains", user_id).stream()
    groups = []
    for g in groups_ref:
        data = g.to_dict()
        role = "leader" if data.get("leader_id") == user_id else "member"
        groups.append({
            "group_id": g.id,
            "group_name": data.get("group_name"),
            "category": data.get("category"),
            "role": role
        })
    return {"status": 200, "list": groups}


'''
(새롭게 추가됨)
'수락' 버튼을 눌렀을 때만 호출됨
이 함수가 기존 join_group이 하던 실제 멤버 추가 로직(배열에 user_id 추가, current_member +1)을 대신 처리
'''
def _add_member_to_group(group_id: str, user_id: str):
    """
    [내부 함수] 사용자를 그룹에 실제로 추가하고 인원수를 늘립니다. (동시성 처리)
    notification_service에서 '수락' 시 호출됩니다.
    """
    doc_ref = db.collection("groups").document(group_id)
    doc = doc_ref.get()
    
    if not doc.exists:
        raise HTTPException(status_code=404, detail="그룹을 찾을 수 없습니다.")
    
    data = doc.to_dict()
    members = data.get("members", [])
    
    if user_id in members:
        raise HTTPException(status_code=400, detail="이미 가입된 회원입니다.")
    
    if len(members) >= data.get("max_member", 10):
        raise HTTPException(status_code=400, detail="정원이 가득 찼습니다.")

    doc_ref.update({
        "members": firestore.ArrayUnion([user_id]),
        "current_member": firestore.Increment(1)
    })
    return {"message": "그룹 가입 처리 완료"}


'''
(기존 코드에서 수정 있음)
사용자를 즉시 추가하는 대신, 초대/신청했다는 액션 문서(group_actions 컬렉션)를 생성
'''
def join_group(group_id: str, user_id: str):
    #(수정됨) 그룹 가입 '신청'을 생성합니다. (status: pending)
    group_ref = db.collection("groups").document(group_id)
    group_doc = group_ref.get()
    if not group_doc.exists:
        raise HTTPException(status_code=404, detail="그룹을 찾을 수 없습니다.")
    
    group_data = group_doc.to_dict()
    leader_id = group_data.get("leader_id")

    action_data = {
        "action_type": "application",
        "group_id": group_id,
        "group_name": group_data.get("group_name"),
        "group_image": group_data.get("group_image"),
        "user_id": user_id,
        "actor_id": user_id,
        "leader_id": leader_id,
        "status": "pending",
        "created_at": datetime.utcnow()
    }
    db.collection("group_actions").document().set(action_data)
    return {"status": 200, "message": "그룹 가입 신청 완료. 팀장의 승인을 기다려주세요."}

'''
(기존 코드에서 수정 있음)
사용자를 즉시 추가하는 대신, 초대/신청했다는 액션 문서(group_actions 컬렉션)를 생성
'''
def invite_member(group_id: str, user_id: str):
    #(수정됨) 그룹 '초대'를 생성합니다. (status: pending)
    group_ref = db.collection("groups").document(group_id)
    group_doc = group_ref.get()
    if not group_doc.exists:
        raise HTTPException(status_code=404, detail="그룹을 찾을 수 없습니다.")
    
    group_data = group_doc.to_dict()
    leader_id = group_data.get("leader_id")
    
    action_data = {
        "action_type": "invite",
        "group_id": group_id,
        "group_name": group_data.get("group_name"),
        "group_image": group_data.get("group_image"),
        "user_id": user_id,
        "actor_id": leader_id,
        "leader_id": leader_id,
        "status": "pending",
        "created_at": datetime.utcnow()
    }
    db.collection("group_actions").document().set(action_data)
    return {"status": 200, "message": f"{user_id}님을 그룹에 초대했습니다."}

def leave_group(group_id: str, user_id: str):
    doc_ref = db.collection("groups").document(group_id)
    doc = doc_ref.get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="그룹을 찾을 수 없습니다.")
    data = doc.to_dict()
    
    if user_id not in data.get("members", []):
        raise HTTPException(status_code=400, detail="가입되지 않은 회원입니다.")
    
    data["members"].remove(user_id)
    doc_ref.update({
        "members": firestore.ArrayRemove([user_id]),
        "current_member": firestore.Increment(-1)
    })
    return {"status": 200, "message": "그룹 탈퇴 완료"}