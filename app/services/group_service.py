from app.config.firebase_config import db
from app.schemas.group_schema import GroupCreate, GroupUpdate
from datetime import datetime
from fastapi import HTTPException

def create_group(group: GroupCreate):
    group_data = group.dict()
    group_data["created_at"] = datetime.utcnow()
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

def get_group_detail(group_id: str):
    doc = db.collection("groups").document(group_id).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="존재하지 않는 그룹입니다.")
    data = doc.to_dict()
    return {
        "status": 200,
        "group_name": data.get("group_name"),
        "category": data.get("category"),
        "max_member": data.get("max_member"),
        "current_member": data.get("current_member"),
        "description": data.get("description"),
        "leader_nickname": data.get("leader_id"),
        "group_image": data.get("group_image")
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

def join_group(group_id: str, user_id: str):
    doc_ref = db.collection("groups").document(group_id)
    doc = doc_ref.get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="그룹을 찾을 수 없습니다.")
    data = doc.to_dict()
    if user_id in data.get("members", []):
        raise HTTPException(status_code=400, detail="이미 가입된 회원입니다.")
    if len(data.get("members", [])) >= data.get("max_member", 10):
        raise HTTPException(status_code=400, detail="정원이 가득 찼습니다.")
    data["members"].append(user_id)
    data["current_member"] = len(data["members"])
    doc_ref.update(data)
    return {"status": 200, "message": "그룹 가입 완료"}

def invite_member(group_id: str, user_id: str):
    # 팀장이 직접 초대하는 경우, join과 거의 동일
    return join_group(group_id, user_id)

def leave_group(group_id: str, user_id: str):
    doc_ref = db.collection("groups").document(group_id)
    doc = doc_ref.get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="그룹을 찾을 수 없습니다.")
    data = doc.to_dict()
    if user_id not in data.get("members", []):
        raise HTTPException(status_code=400, detail="가입되지 않은 회원입니다.")
    data["members"].remove(user_id)
    data["current_member"] = len(data["members"])
    doc_ref.update(data)
    return {"status": 200, "message": "그룹 탈퇴 완료"}
