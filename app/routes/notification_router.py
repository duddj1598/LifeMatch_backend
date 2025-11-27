from fastapi import APIRouter, HTTPException, Depends
from app.schemas.notification_schema import NotificationsListResponse, RespondToAction
from app.services import notification_service
from app.middleware.auth import get_current_user

router = APIRouter(
    prefix="/api/notifications",
    tags=["Notifications"]
)


# -------------------------------------------------
# 🔒 알림 목록 조회
# -------------------------------------------------
@router.get(
    "/",
    response_model=NotificationsListResponse,
    summary="알림 페이지 목록 조회 (초대/신청자)"
)
def get_my_notifications(current_user: dict = Depends(get_current_user)):
    """
    JWT에서 user_doc_id를 가져와서
    - 내가 받은 초대
    - 내 그룹의 신청자 (내가 리더인 그룹)
    조회
    """
    try:
        user_id = current_user["user_doc_id"]
        return notification_service.get_all_notifications(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -------------------------------------------------
# 🔒 초대/신청에 응답 (수락/거절)
# -------------------------------------------------
@router.post(
    "/{action_id}/respond",
    summary="초대/신청 요청 처리"
)
def respond_to_notification(
    action_id: str,
    request_body: RespondToAction,
    current_user: dict = Depends(get_current_user)
):
    """
    수락/거절은 반드시 JWT에 있는 현재 로그인 유저만 가능함.
    request_body.user_id는 무시하고 보안 위해 서버에서 덮어씀.
    """
    try:
        actor_user_id = current_user["user_doc_id"]  # JWT 기반
        return notification_service.respond_to_action(
            action_id=action_id,
            actor_user_id=actor_user_id,
            action=request_body.action
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
