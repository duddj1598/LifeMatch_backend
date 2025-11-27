from app.config.firebase_config import db
from app.schemas.home_schema import (
    RecommendedActivity, HomeData, HomeResponse,
    OtherRecommendationsResponse
)
import random

TYPE_TO_CATEGORY_MAP = {
    "자기관리형 웰니스족": "생활습관·건강",
    "디지털 트렌드세터": "기술",
    "알뜰살뜰 실속파": "소비·경제",
    "감성 충만 아티스트": "여가·문화",
    "소박한 힐링주의자": "여가·문화"
}

DEFAULT_CATEGORY = "여가·문화"


# -------------------------------------------------
# 내부 유저 데이터 + 유형 카테고리 변환
# -------------------------------------------------
def _get_user_info_and_category(user_id: str):
    user_ref = db.collection("users").document(user_id)
    user_doc = user_ref.get()

    if not user_doc.exists:
        raise Exception("User not found")

    user_data = user_doc.to_dict()
    user_type = user_data.get("user_lifestyle_type")

    # 유형에 맞는 추천 카테고리
    if user_type in TYPE_TO_CATEGORY_MAP:
        target_category = TYPE_TO_CATEGORY_MAP[user_type]
    else:
        target_category = DEFAULT_CATEGORY
        user_type = "방문자"

    return user_data, user_type, target_category


# -------------------------------------------------
# 🔒 본인 유형 기반 추천 활동 2개 조회
# -------------------------------------------------
def get_home_recommendations(user_id: str) -> dict:
    _, user_type, target_category = _get_user_info_and_category(user_id)

    activities = []
    exclude_ids = set()

    # 🔹 1. 메인 쿼리: 2개가 아니라 넉넉하게 5~10개를 가져옵니다.
    # (내 그룹이 섞여 있을 경우를 대비해 여유분을 가져오는 것)
    query = db.collection("groups")\
        .where("category", "==", target_category)\
        .limit(10) 
        
    for doc in query.stream():
        # 2개가 다 찼으면 그만 찾기
        if len(activities) >= 2:
            break

        group_data = doc.to_dict()
        leader_id = group_data.get("leader_id")

        # 🚨 [핵심 필터링] 내가 리더인 그룹은 리스트에 넣지 않고 건너뜀!
        if leader_id == user_id:
            continue

        activities.append(
            RecommendedActivity(
                group_id=doc.id,
                group_name=group_data.get("group_name", "이름 없는 모임"),
                category=group_data.get("category"),
                leader_id=leader_id
            )
        )
        exclude_ids.add(doc.id)

    # 🔹 2. Fallback: 부족하면 기본 카테고리에서 채우기
    # (여기서도 마찬가지로 내 그룹은 제외해야 함)
    if len(activities) < 2:
        needed = 2 - len(activities)
        # 여기서도 넉넉하게 가져옴 (필요한 개수 + 5개 정도 여유)
        fallback = db.collection("groups")\
            .where("category", "==", DEFAULT_CATEGORY)\
            .limit(needed + 5) 
            
        for doc in fallback.stream():
            if len(activities) >= 2:
                break

            # 이미 뽑은 거면 패스
            if doc.id in exclude_ids:
                continue

            group_data = doc.to_dict()
            leader_id = group_data.get("leader_id")

            # 🚨 [핵심 필터링] 여기서도 내 그룹은 제외
            if leader_id == user_id:
                continue

            activities.append(
                RecommendedActivity(
                    group_id=doc.id,
                    group_name=group_data.get("group_name", "이름 없는 모임"),
                    category=group_data.get("category"),
                    leader_id=leader_id
                )
            )

    home_data = HomeData(
        user_lifestyle_type=user_type,
        recommended_activities=activities
    )

    return HomeResponse(status=200, data=home_data).dict()


# -------------------------------------------------
# 🔒 "다른 유형" 추천 활동 목록
# -------------------------------------------------
def get_other_recommendations(user_id: str) -> dict:
    _, _, target_category = _get_user_info_and_category(user_id)

    all_categories = set(TYPE_TO_CATEGORY_MAP.values())
    other_categories = list(all_categories - {target_category})

    if not other_categories:
        other_categories = list(all_categories)

    random.shuffle(other_categories)

    other_activities = []

    for c in other_categories:
        doc = next(db.collection("groups").where("category", "==", c).limit(1).stream(), None)
        if doc:
            g = doc.to_dict()
            other_activities.append(
                RecommendedActivity(
                    group_id=doc.id,
                    group_name=g.get("group_name", "이름 없는 모임"),
                    category=g.get("category"),
                    leader_id=g.get("leader_id")
                )
            )

    return OtherRecommendationsResponse(status=200, data=other_activities).dict()
