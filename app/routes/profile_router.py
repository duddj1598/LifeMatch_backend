from fastapi import APIRouter, HTTPException, Depends
from app.schemas.profile_schema import ProfileResponse, ProfileUpdate, NotificationSettings
from app.services import profile_service
from app.middleware.auth import get_current_user

router = APIRouter(
    prefix="/api/user",
    tags=["UserProfile"]
)


# -------------------------------------------------
# 🔒 마이페이지 메인 화면 조회
# -------------------------------------------------
@router.get(
    "/profile",
    response_model=ProfileResponse,
    summary="[마이페이지] 메인 화면 조회"
)
def get_profile(current_user: dict = Depends(get_current_user)):
    """
    프론트는 user_id를 보내지 않음.
    JWT에서 현재 로그인 사용자 Firestore 문서 ID만 사용.
    """
    try:
        user_id = current_user["user_doc_id"]
        return profile_service.get_user_profile(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -------------------------------------------------
# 🔒 프로필 수정 (닉네임, 이미지, 선호 카테고리)
# -------------------------------------------------
@router.patch(
    "/profile",
    summary="[프로필 수정] '저장'"
)
def update_profile(
    data: ProfileUpdate,
    current_user: dict = Depends(get_current_user)
):
    """
    user_id는 프론트에서 절대 전달하지 않는다.
    """
    try:
        user_id = current_user["user_doc_id"]
        return profile_service.update_user_profile(user_id, data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -------------------------------------------------
# 🔒 알림 설정 (On/Off)
# -------------------------------------------------
@router.patch(
    "/settings/notifications",
    summary="[알림 설정] On/Off 토글 저장"
)
def update_notifications(
    settings: NotificationSettings,
    current_user: dict = Depends(get_current_user)
):
    try:
        user_id = current_user["user_doc_id"]
        return profile_service.update_notification_settings(user_id, settings)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
