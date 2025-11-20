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

def _get_user_info_and_category(user_id: str) -> tuple[dict, str, str]:
    """(내부용 함수) 사용자 정보와 타겟 카테고리를 조회합니다."""
    user_ref = db.collection("users").document(user_id)
    user_doc = user_ref.get()

    if not user_doc.exists:
        raise Exception("User not found")

    user_data = user_doc.to_dict()
    user_type = user_data.get("user_lifestyle_type")

    if user_type and user_type in TYPE_TO_CATEGORY_MAP:
        target_category = TYPE_TO_CATEGORY_MAP[user_type]
    else:
        target_category = DEFAULT_CATEGORY
        user_type = "방문자"
        
    return user_data, user_type, target_category

def get_home_recommendations(user_id: str) -> dict:
    
    try:
        _, user_type, target_category = _get_user_info_and_category(user_id)
    except Exception as e:
        raise e

    activities = []
    exclude_ids = set()

    query = db.collection("groups").where("category", "==", target_category).limit(2)
    group_docs = query.stream()

    for doc in group_docs:
        group_data = doc.to_dict()
        activity = RecommendedActivity(
            group_id=doc.id,
            group_name=group_data.get("group_name", "이름 없는 모임"),
            category=group_data.get("category")
        )
        activities.append(activity)
        exclude_ids.add(doc.id)

    num_needed = 2 - len(activities)
    
    if num_needed > 0 and target_category != DEFAULT_CATEGORY:
        fallback_query = db.collection("groups").where("category", "==", DEFAULT_CATEGORY).limit(num_needed)
        fallback_docs = fallback_query.stream()
        
        for doc in fallback_docs:
            if doc.id not in exclude_ids:
                group_data = doc.to_dict()
                activity = RecommendedActivity(
                    group_id=doc.id,
                    group_name=group_data.get("group_name", "이름 없는 모임"),
                    category=group_data.get("category")
                )
                activities.append(activity)
                exclude_ids.add(doc.id)
                if len(activities) == 2:
                    break

    home_data = HomeData(
        user_lifestyle_type=user_type,
        recommended_activities=activities
    )
    
    return HomeResponse(status=200, data=home_data).dict()


def get_other_recommendations(user_id: str) -> dict:
    """
    (신규)
    '다른' 유형에게 추천되는 활동 목록을 반환합니다.
    사용자의 타겟 카테고리를 제외한 나머지 카테고리에서 1개씩 가져옵니다.
    """
    
    try:
        _, _, target_category = _get_user_info_and_category(user_id)
    except Exception as e:
        raise e

    all_categories = set(TYPE_TO_CATEGORY_MAP.values())
    
    other_categories = list(all_categories - {target_category})
    
    if not other_categories:
        other_categories = list(all_categories)
        
    random.shuffle(other_categories)

    other_activities = []
    
    for category_name in other_categories:
        query = db.collection("groups").where("category", "==", category_name).limit(1)
        doc = next(query.stream(), None)
        
        if doc:
            group_data = doc.to_dict()
            activity = RecommendedActivity(
                group_id=doc.id,
                group_name=group_data.get("group_name", "이름 없는 모임"),
                category=group_data.get("category")
            )
            other_activities.append(activity)

    return OtherRecommendationsResponse(
        status=200,
        data=other_activities
    ).dict()