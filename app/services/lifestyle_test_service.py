from app.config.firebase_config import db

ALL_LIFESTYLE_TYPES_DATA = [
    {
        "type_name": "자기관리형 웰니스족",
        "keywords": "#갓생 #건강 #피트니스 #성장",
        "description": "건강한 식단과 꾸준한 운동을 즐기며..."
    },
    {
        "type_name": "디지털 트렌드세터",
        "keywords": "#신상 #IT #핫플 #AI #소비",
        "description": "최신 기술과 트렌드에 민감하며..."
    },
    {
        "type_name": "알뜰살뜰 실속파",
        "keywords": "#가성비 #절약 #포인트 #합리적",
        "description": "합리적인 소비 생활을 실천하며..."
    },
    {
        "type_name": "감성 충만 아티스트",
        "keywords": "#취향 #문화생활 #여행 #디자인",
        "description": "감성과 취향을 중시하며..."
    },
    {
        "type_name": "소박한 힐링주의자",
        "keywords": "#휴식 #자연 #집콕 #안정",
        "description": "편안하고 안정적인 삶을 선호하며..."
    }
]


TYPE_SCORING_MAP_COMPLEX = {
    "자기관리형 웰니스족": [2, 9, 10, 12],
    "디지털 트렌드세터":   [1, 3, 5, 7, 9, 11, 13],
    "알뜰살뜰 실속파":     [2, 4, 11, 14, 15],
    "감성 충만 아티스트":   [1, 5, 8, 12],
    "소박한 힐링주의자":   [6, 8, 10, 12, 14, 16]
}


# -------------------------------------------------
# 질문 조회
# -------------------------------------------------

def get_test_questions():
    """(생략) 기존 코드 그대로 유지"""
    # ... 너의 mock_data 그대로 사용
    from .mock_questions import mock_data   # 예시 파일 구조일 경우
    return mock_data


# -------------------------------------------------
# 라이프 스타일 타입 목록 조회
# -------------------------------------------------

def get_lifestyle_types():
    return {
        "status": 200,
        "data": ALL_LIFESTYLE_TYPES_DATA
    }


# -------------------------------------------------
# 🔥 핵심: 검사지 제출 + Firestore 저장
# -------------------------------------------------

def process_test_results(user_doc_id: str, selected_ids: list) -> dict:
    """
    JWT에서 얻은 Firestore user_doc_id와 선택된 option_ids로
    - 유형 계산
    - Firestore 저장
    - 결과 반환
    """
    # --- 1) 점수 계산 ---
    scores = {type_name: 0 for type_name in TYPE_SCORING_MAP_COMPLEX.keys()}

    for option_id in selected_ids:
        for type_name, scoring_ids in TYPE_SCORING_MAP_COMPLEX.items():
            if option_id in scoring_ids:
                scores[type_name] += 1

    highest_type = max(scores, key=scores.get)
    if scores[highest_type] == 0:
        highest_type = "소박한 힐링주의자"

    # --- 2) 상세 정보 매칭 ---
    result_detail = next(
        (t for t in ALL_LIFESTYLE_TYPES_DATA if t["type_name"] == highest_type),
        ALL_LIFESTYLE_TYPES_DATA[2]
    )

    # --- 3) Firestore 저장 ---
    try:
        user_ref = db.collection("users").document(user_doc_id)
        user_ref.update({
            "user_lifestyle_type": highest_type,
            "user_survey_response": {"selected_option_ids": selected_ids}
        })
    except Exception as e:
        print("Error saving lifestyle result:", e)

    # --- 4) 반환 ---
    return {
        "status": 200,
        "user_id": user_doc_id,
        "result": result_detail
    }
