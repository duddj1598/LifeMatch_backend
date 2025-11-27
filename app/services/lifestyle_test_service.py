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

def get_test_questions() -> dict:
    """
    API 명세서의 예시 데이터를 기반으로 유형 검사 질문 목록을 반환합니다.
    """
    mock_data = {
        "status": 200,
        "data": {
            "part1": [
                {
                    "question_id": 1,
                    "question_text": "나의 소비 스타일은?",
                    "options": [
                        { "option_id": 1, "text": "새로운 경험을 위해서라면! 일단 결제하고 본다" }, # 트렌드세터, 아티스트
                        { "option_id": 2, "text": "이걸 사는 게 맞을까? 가성비를 꼼꼼히 따져본다" }  # 실속파, 웰니스족
                    ]
                },
                {
                    "question_id": 2,
                    "question_text": "더 끌리는 아이템은?",
                    "options": [
                        { "option_id": 3, "text": "최신 유행하는 신상 아이템" }, # 트렌드세터
                        { "option_id": 4, "text": "오래 쓸 수 있는 클래식 아이템" } # 실속파
                    ]
                }
            ],
            "part2": [
                {
                    "question_id": 3,
                    "question_text": "주말에 약속이 없다면?",
                    "options": [
                        { "option_id": 5, "text": "핫한 팝업스토어로 향한다" }, # 트렌드세터, 아티스트
                        { "option_id": 6, "text": "밀린 드라마를 정주행하며 집콕한다" } # 힐링주의자
                    ]
                },
                {
                    "question_id": 4,
                    "question_text": "여행을 떠난다면?",
                    "options": [
                        { "option_id": 7, "text": "SNS에 뜨는 명소 중심으로!" }, # 트렌드세터
                        { "option_id": 8, "text": "나만 아는 조용한 곳으로!" } # 힐링주의자, 아티스트
                    ]
                }
            ],
            "part3": [
                {
                    "question_id": 5,
                    "question_text": "오늘 운동 뭐 하지?",
                    "options": [
                        { "option_id": 9, "text": "인기 많은 피트니스 클래스를 찾아본다" }, # 트렌드세터, 웰니스족
                        { "option_id": 10, "text": "상쾌하게 공원에서 조깅이나 할까" } # 힐링주의자, 웰니스족
                    ]
                },
                {
                    "question_id": 6,
                    "question_text": "스트레스 받을 땐?",
                    "options": [
                        { "option_id": 11, "text": "매운 음식을 먹거나 쇼핑으로 푼다" }, # 트렌드세터, 실속파
                        { "option_id": 12, "text": "명상을 하거나 좋아하는 음악을 듣는다" } # 웰니스족, 아티스트, 힐링주의자
                    ]
                }
            ],
            "part4": [
                {
                    "question_id": 7,
                    "question_text": "새로운 기술이 나오면?",
                    "options": [
                        { "option_id": 13, "text": "일단 써봐야 직성이 풀린다" }, # 트렌드세터
                        { "option_id": 14, "text": "안정성이 검증될 때까지 기다린다" } # 실속파, 힐링주의자
                    ]
                },
                {
                    "question_id": 8,
                    "question_text": "안 쓰는 물건이 생기면?",
                    "options": [
                        { "option_id": 15, "text": "중고거래 앱에 바로 올린다" }, # 실속파
                        { "option_id": 16, "text": "언젠가 쓸 것 같아 일단 둔다" } # 힐링주의자
                    ]
                }
            ]
        }
    }
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
