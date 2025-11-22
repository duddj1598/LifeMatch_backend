from app.config.firebase_config import db
from app.schemas.profile_schema import (
    ProfileResponse, ProfileUpdate, NotificationSettings,
    LifestyleTypeInfo, ActivityReport
)
from fastapi import HTTPException
from typing import Optional, Dict

from app.services.lifestyle_test_service import ALL_LIFESTYLE_TYPES_DATA


# -------------------------------------------------
# 라이프스타일 상세 정보 매핑
# -------------------------------------------------
def _get_lifestyle_details(type_name: str) -> Optional[LifestyleTypeInfo]:
    if not type_name:
        return None

    for t in ALL_LIFESTYLE_TYPES_DATA:
        if t["type_name"] == type_name:
            return LifestyleTypeInfo(**t)

    return None


# -------------------------------------------------
# 🔒 프로필 조회
# -------------------------------------------------
def get_user_profile(user_id: str) -> dict:
    user_ref = db.collection("users").document(user_id)
    user_doc = user_ref.get()

    if not user_doc.exists:
        raise HTTPException(status_code=404, detail="User not found")

    user_data = user_doc.to_dict()

    # 라이프스타일 정보 매핑
    life_type = user_data.get("user_lifestyle_type")
    lifestyle_info = _get_lifestyle_details(life_type)

    # 활동 리포트(현재 mock)
    activity_report = ActivityReport(
        monthly_participation_count=4,
        recent_participation_rate=0.75,
        most_active_category="여가·문화"
    )

    notification_settings = NotificationSettings(
        notification_enabled=user_data.get("notification_enabled", True)
    )

    activity_preferences = user_data.get("activity_preferences", {})

    response = ProfileResponse(
        user_nickname=user_data.get("user_nickname", "닉네임 없음"),
        user_email=user_data.get("user_email"),
        profile_image=user_data.get("profile_image"),
        lifestyle_info=lifestyle_info,
        activity_report=activity_report,
        notification_settings=notification_settings,
        activity_preferences=activity_preferences,
    )

    return response.dict()


# -------------------------------------------------
# 🔒 프로필 수정
# -------------------------------------------------
def update_user_profile(user_id: str, data: ProfileUpdate) -> dict:
    user_ref = db.collection("users").document(user_id)

    if not user_ref.get().exists:
        raise HTTPException(status_code=404, detail="User not found")

    update_data = data.dict(exclude_unset=True)

    if not update_data:
        raise HTTPException(status_code=400, detail="수정할 내용이 없습니다.")

    user_ref.update(update_data)

    return {"status": 200, "message": "프로필 수정 완료"}


# -------------------------------------------------
# 🔒 알림 설정 변경
# -------------------------------------------------
def update_notification_settings(user_id: str, data: NotificationSettings) -> dict:
    user_ref = db.collection("users").document(user_id)

    if not user_ref.get().exists:
        raise HTTPException(status_code=404, detail="User not found")

    user_ref.update({
        "notification_enabled": data.notification_enabled
    })

    return {"status": 200, "message": "알림 설정 변경 완료"}
