from fastapi import APIRouter, HTTPException, Query, Body
from app.schemas.notification_schema import NotificationsListResponse, RespondToAction
from app.services import notification_service

router = APIRouter(
    prefix="/api/notifications",
    tags=["Notifications"]
)

@router.get(
    "/",
    response_model=NotificationsListResponse,
    summary="알림 페이지 목록 조회 (초대/신청자)"
)
def get_my_notifications(user_id: str = Query(..., description="로그인한 사용자 ID")):
    """
    알림 페이지에 표시될 2가지 목록 반환
    1. 내가 받은 '소모임 초대'
    2. 내 소모임의 '소모임 신청자'
    """
    try:
        results = notification_service.get_all_notifications(user_id)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post(
    "/{action_id}/respond",
    summary="초대/신청에 응답 (수락/거절)"
)
def respond_to_notification(
    action_id: str,
    response: RespondToAction = Body(...)
):
    try:
        result = notification_service.respond_to_action(
            action_id,
            response.user_id,
            response.action
        )
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))