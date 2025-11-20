from app.config.firebase_config import db
from app.services.group_service import _add_member_to_group
from fastapi import HTTPException
from google.cloud.firestore_v1.base_query import FieldFilter
from typing import List

from app.schemas.notification_schema import (
    GroupInviteNotification, GroupApplicantNotification, NotificationsListResponse
)

#알림 페이지에 표시될 '초대'와 '신청자' 목록 조회
def get_all_notifications(user_id: str) -> dict:
    invites = _get_pending_invites(user_id)
    applicants = _get_pending_applicants(user_id)
    
    return NotificationsListResponse(
        status=200,
        invites=invites,
        applicants=applicants
    ).dict()


def _get_pending_invites(user_id: str) -> List[GroupInviteNotification]:
    actions_ref = db.collection("group_actions")
    query = actions_ref.where(filter=FieldFilter("user_id", "==", user_id)) \
                       .where(filter=FieldFilter("action_type", "==", "invite")) \
                       .where(filter=FieldFilter("status", "==", "pending"))
    
    invite_list = []
    for doc in query.stream():
        data = doc.to_dict()
        group_doc = db.collection("groups").document(data["group_id"]).get()
        group_data = group_doc.to_dict() if group_doc.exists else {}

        invite_list.append(
            GroupInviteNotification(
                action_id=doc.id,
                group_id=data["group_id"],
                group_name=data.get("group_name", "모임 이름 없음"),
                group_image=data.get("group_image"),
                group_subject=group_data.get("category")
            )
        )
    return invite_list

#내 소모임의 '소모임 신청자' 목록 조회
def _get_pending_applicants(user_id: str) -> List[GroupApplicantNotification]:
    actions_ref = db.collection("group_actions")
    query = actions_ref.where(filter=FieldFilter("leader_id", "==", user_id)) \
                       .where(filter=FieldFilter("action_type", "==", "application")) \
                       .where(filter=FieldFilter("status", "==", "pending"))

    applicant_list = []
    for doc in query.stream():
        data = doc.to_dict()
        
        # 신청자 정보 조회
        applicant_id = data["user_id"]
        user_doc = db.collection("users").document(applicant_id).get()
        user_data = user_doc.to_dict() if user_doc.exists else {}

        applicant_list.append(
            GroupApplicantNotification(
                action_id=doc.id,
                group_id=data["group_id"],
                group_name=data.get("group_name", "모임 이름 없음"),
                group_image=data.get("group_image"),
                applicant_id=applicant_id,
                applicant_nickname=user_data.get("user_nickname", "닉네임 없음"),
                applicant_interest=user_data.get("user_lifestyle_type", "유형 없음")
            )
        )
    return applicant_list

#수락/거절
def respond_to_action(action_id: str, actor_user_id: str, action: str):
    action_ref = db.collection("group_actions").document(action_id)
    action_doc = action_ref.get()

    if not action_doc.exists:
        raise HTTPException(status_code=404, detail="존재하지 않는 요청입니다.")
    
    data = action_doc.to_dict()
    
    if data["status"] != "pending":
        raise HTTPException(status_code=400, detail="이미 처리된 요청입니다.")

    action_type = data["action_type"]
    user_to_add = data["user_id"]
    group_id = data["group_id"]

    if action_type == "invite":
        if data["user_id"] != actor_user_id:
            raise HTTPException(status_code=403, detail="초대에 응답할 권한이 없습니다.")
    elif action_type == "application":
        if data["leader_id"] != actor_user_id:
            raise HTTPException(status_code=403, detail="신청을 처리할 권한이 없습니다.")
    
    if action == "accept":
        try:
            _add_member_to_group(group_id, user_to_add)
            action_ref.update({"status": "accepted"})
            return {"status": 200, "message": "요청을 수락했습니다."}
        except Exception as e:
            raise HTTPException(status_code=e.status_code if hasattr(e, 'status_code') else 500, 
                                detail=e.detail if hasattr(e, 'detail') else f"멤버 추가 중 오류: {str(e)}")
            
    elif action == "decline":
        action_ref.update({"status": "declined"})
        return {"status": 200, "message": "요청을 거절했습니다."}
    
    else:
        raise HTTPException(status_code=400, detail="잘못된 action 값입니다. 'accept' 또는 'decline'만 가능합니다.")