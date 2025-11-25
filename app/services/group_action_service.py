from app.config.firebase_config import db
from fastapi import HTTPException
from google.cloud import firestore

from app.schemas.group_action_schema import (
    GroupInviteRequest,
    GroupInviteResponse,
    GroupApplyRequest,
    GroupApplyResponse
)


# ---------------------------------------------
# 🔧 Firestore user_id → Firestore 문서 ID 변환
# ---------------------------------------------
def resolve_firestore_user_doc_id(user_id: str):
    """
    프론트에서 전달된 user_id(예: 'ww') → Firestore 문서 ID(doc.id)로 변환
    """
    query = db.collection("users").where("user_id", "==", user_id).stream()
    docs = list(query)
    if not docs:
        return None
    return docs[0].id  # Firestore 문서 ID 반환


# ---------------------------------------------
# 🔥 1. 그룹 초대 (리더 → 유저)
# ---------------------------------------------
def invite_user_to_group(req: GroupInviteRequest):

    group_id = req.group_id
    raw_user_id = req.user_id  # 프론트에서 보낸 user_id (내부 id)

    # 1) Firestore 문서 ID로 변환
    target_user_doc_id = resolve_firestore_user_doc_id(raw_user_id)
    if not target_user_doc_id:
        raise HTTPException(status_code=404, detail="해당 유저를 찾을 수 없습니다.")

    # 2) 그룹 확인
    group_doc = db.collection("groups").document(group_id).get()
    if not group_doc.exists:
        raise HTTPException(status_code=404, detail="해당 그룹이 존재하지 않습니다.")

    group_data = group_doc.to_dict()
    leader_id = group_data.get("leader_id")

    # 3) 초대 액션 생성
    action_data = {
        "group_id": group_id,
        "group_name": group_data.get("group_name"),
        "group_image": group_data.get("group_image"),
        "leader_id": leader_id,
        "user_id": target_user_doc_id,
        "action_type": "invite",   # 🔥 구분
        "status": "pending",
        "created_at": firestore.SERVER_TIMESTAMP,
    }

    # 저장
    doc_ref = db.collection("group_actions").document()
    doc_ref.set(action_data)

    return GroupInviteResponse(
        status=200,
        message="초대가 성공적으로 전송되었습니다.",
        action_id=doc_ref.id
    )


# ---------------------------------------------
# 🔥 2. 그룹 가입 신청 (유저 → 리더)
# ---------------------------------------------
def apply_to_join_group(req: GroupApplyRequest):

    group_id = req.group_id
    raw_user_id = req.user_id  # 프론트에서 보낸 user_id (내부 id)

    # 1) Firestore 문서 ID 찾기
    applicant_doc_id = resolve_firestore_user_doc_id(raw_user_id)
    if not applicant_doc_id:
        raise HTTPException(status_code=404, detail="해당 유저를 찾을 수 없습니다.")

    # 2) 그룹 존재 확인
    group_doc = db.collection("groups").document(group_id).get()
    if not group_doc.exists:
        raise HTTPException(status_code=404, detail="해당 그룹이 존재하지 않습니다.")

    group_data = group_doc.to_dict()
    leader_id = group_data.get("leader_id")
    if not leader_id:
        raise HTTPException(status_code=400, detail="리더 ID가 없습니다.")

    # 3) 가입 신청 액션 생성
    action_data = {
        "group_id": group_id,
        "group_name": group_data.get("group_name"),
        "group_image": group_data.get("group_image"),
        "leader_id": leader_id,         # 🔥 리더에게 알림 가야함
        "user_id": applicant_doc_id,    # 🔥 신청한 사람 (Firestore 문서 ID)
        "action_type": "application",   # 🔥 구분
        "status": "pending",
        "created_at": firestore.SERVER_TIMESTAMP,
    }

    # 저장
    doc_ref = db.collection("group_actions").document()
    doc_ref.set(action_data)

    return GroupApplyResponse(
        status=200,
        message="가입 신청이 성공적으로 전송되었습니다.",
        action_id=doc_ref.id
    )
