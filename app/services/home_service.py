from app.config.firebase_config import db
from app.schemas.home_schema import (
    RecommendedActivity, HomeData, HomeResponse, 
    OtherRecommendationsResponse 
)
import random 

# 1. 사용자의 '라이프스타일 유형'을 '그룹 카테고리'로 변환하는 맵(MAP)을 정의합니다.
TYPE_TO_CATEGORY_MAP = {
    "자기관리형 웰니스족": "생활습관·건강",
    "디지털 트렌드세터": "기술",
    "알뜰살뜰 실속파": "소비·경제",
    "감성 충만 아티스트": "여가·문화",
    "소박한 힐링주의자": "여가·문화"
}

# 기본 카테고리 (유형이 없거나 매핑되는 카테고리가 없을 경우 + 폴백 로직)
DEFAULT_CATEGORY = "여가·문화"

def _get_user_info_and_category(user_id: str) -> tuple[dict, str, str]: # 👈 (수정됨)
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
    """
    (수정됨)
    사용자 유형에 맞는 추천 2개를 가져옵니다.
    만약 2개가 채워지지 않으면 '기본 카테고리'에서 부족한 만큼 채웁니다.
    """
    
    try:
        _, user_type, target_category = _get_user_info_and_category(user_id)
    except Exception as e:
        raise e # User not found

    activities = []
    exclude_ids = set() # 중복 추천을 방지하기 위한 set

    # 1. (1차 시도) 사용자의 '타겟 카테고리'에서 2개 검색
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

    # 2. (2차 시도 - Fallback) 1차에서 2개를 못 채웠다면, '기본 카테고리'에서 마저 채움
    num_needed = 2 - len(activities)
    
    if num_needed > 0 and target_category != DEFAULT_CATEGORY:
        # 타겟 카테고리가 기본 카테고리와 다를 때만 2차 시도
        fallback_query = db.collection("groups").where("category", "==", DEFAULT_CATEGORY).limit(num_needed)
        fallback_docs = fallback_query.stream()
        
        for doc in fallback_docs:
            if doc.id not in exclude_ids: # 중복 방지
                group_data = doc.to_dict()
                activity = RecommendedActivity(
                    group_id=doc.id,
                    group_name=group_data.get("group_name", "이름 없는 모임"),
                    category=group_data.get("category")
                )
                activities.append(activity)
                exclude_ids.add(doc.id)
                if len(activities) == 2:
                    break # 2개를 다 채웠으면 종료

    # 3. 최종 응답 데이터를 조립합니다.
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
        raise e # User not found

    # 1. 전체 카테고리 목록 (중복 제거)
    all_categories = set(TYPE_TO_CATEGORY_MAP.values())
    
    # 2. 사용자의 타겟 카테고리를 '제외한' 다른 카테고리 목록
    other_categories = list(all_categories - {target_category})
    
    # (예외 처리) 만약 모든 유형이 1개 카테고리로 매핑되면, 그냥 전체 카테고리 사용
    if not other_categories:
        other_categories = list(all_categories)
        
    random.shuffle(other_categories) # 카테고리 순서를 섞어 매번 다른 추천이 나오게 함

    other_activities = []
    
    # 3. 다른 카테고리들을 순회하며 그룹을 1개씩 검색
    for category_name in other_categories:
        query = db.collection("groups").where("category", "==", category_name).limit(1)
        doc = next(query.stream(), None) # 결과가 0개면 None 반환
        
        if doc:
            group_data = doc.to_dict()
            activity = RecommendedActivity(
                group_id=doc.id,
                group_name=group_data.get("group_name", "이름 없는 모임"),
                category=group_data.get("category")
            )
            other_activities.append(activity)

    # 4. 최종 응답 데이터를 조립합니다.
    return OtherRecommendationsResponse(
        status=200,
        data=other_activities
    ).dict()