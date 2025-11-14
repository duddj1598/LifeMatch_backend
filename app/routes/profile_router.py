from fastapi import APIRouter, HTTPException, Path, Body
from app.schemas.profile_schema import ProfileResponse, ProfileUpdate, NotificationSettings
from app.services import profile_service

router = APIRouter(
    prefix="/api/user",
    tags=["UserProfile"]
)

@router.get(
    "/{user_id}/profile",
    response_model=ProfileResponse,
    summary="[마이페이지] 메인 화면 조회"
)
def get_profile(user_id: str = Path(..., description="사용자 ID")):
    try:
        return profile_service.get_user_profile(user_id)
    except Exception as e:
        raise HTTPException(status_code=getattr(e, 'status_code', 500), detail=str(e))

@router.patch(
    "/{user_id}/profile",
    summary="[프로필 수정] '저장' (닉네임, 사진, 선호도)"
)
def update_profile(
    user_id: str = Path(..., description="사용자 ID"),
    profile_data: ProfileUpdate = Body(...)
):
    try:
        return profile_service.update_user_profile(user_id, profile_data)
    except Exception as e:
        raise HTTPException(status_code=getattr(e, 'status_code', 500), detail=str(e))

@router.patch(
    "/{user_id}/settings/notifications",
    summary="[알림 설정] On/Off 토글 저장"
)
def update_notifications(
    user_id: str = Path(..., description="사용자 ID"),
    settings: NotificationSettings = Body(...)
):
    try:
        return profile_service.update_notification_settings(user_id, settings)
    except Exception as e:
        raise HTTPException(status_code=getattr(e, 'status_code', 500), detail=str(e))