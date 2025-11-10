from app.config.firebase_config import db 

from app.schemas.lifestyle_test_schema import (
    LifestyleQuestionsResponse, LifestyleTypesResponse, 
    LifestyleTestSubmission, LifestyleTestResultResponse,
    QuestionParts, Question, QuestionOption, LifestyleTypeDetail, 
    LifestyleTestResultDetail
)

ALL_LIFESTYLE_TYPES_DATA = [
    {
        "type_name": "자기관리형 웰니스족",
        "keywords": "#갓생 #건강 #피트니스 #성장",
        "description": "건강한 식단과 꾸준한 운동을 즐기며, 몸과 마음의 건강을 최우선으로 생각하는 유형입니다. 자기계발에도 관심이 많아 늘 새로운 것을 배우고 성장하는 것을 추구합니다."
    },
    {
        "type_name": "디지털 트렌드세터",
        "keywords": "#신상 #IT #핫플 #AI #소비",
        "description": "최신 기술과 트렌드에 민감하며, 새로 나온 서비스나 AI 챗봇 등을 적극적으로 사용합니다. 핫플레이스를 찾아다니고 유행하는 아이템을 소비하며 트렌드를 주도하는 유형입니다."
    },
    {
        "type_name": "알뜰살뜰 실속파",
        "keywords": "#가성비 #절약 #포인트 #합리적",
        "description": "소비를 할 때 가성비와 실용성을 중요하게 생각합니다. 포인트 적립, 중고 거래 등을 통해 합리적인 소비 생활을 실천하며, 계획적으로 돈을 관리하는 데 능숙한 유형입니다."
    },
    {
        "type_name": "감성 충만 아티스트",
        "keywords": "#취향 #문화생활 #여행 #디자인",
        "description": "나만의 확고한 취향을 가지고 있으며, 영화, 전시, 음악 등 문화예술을 즐깁니다. 즉흥적인 여행을 떠나거나 예쁜 카페를 찾아다니며 일상 속에서 감성과 영감을 중요시하는 유형입니다."
    },
    {
        "type_name": "소박한 힐링주의자",
        "keywords": "#휴식 #자연 #집콕 #안정",
        "description": "화려함보다는 편안하고 안정적인 삶을 선호합니다. 집에서 OTT를 보거나 반려동물과 시간을 보내는 것을 즐기며, 자연 속에서 여유를 찾으며 소박한 행복을 추구합니다."
    }
]


TYPE_SCORING_MAP_COMPLEX = {
    "자기관리형 웰니스족": [2, 9, 10, 12],
    "디지털 트렌드세터":   [1, 3, 5, 7, 9, 11, 13],
    "알뜰살뜰 실속파":   [2, 4, 11, 14, 15],
    "감성 충만 아티스트":   [1, 5, 8, 12],
    "소박한 힐링주의자":   [6, 8, 10, 12, 14, 16]
}


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

def get_lifestyle_types() -> dict:
    """
    API 명세서의 예시 데이터를 기반으로 전체 라이프스타일 유형을 반환합니다.
    (전역 변수 ALL_LIFESTYLE_TYPES_DATA 를 사용)
    """
    return {
        "status": 200,
        "data": ALL_LIFESTYLE_TYPES_DATA
    }

def process_test_results(submission: LifestyleTestSubmission) -> dict:
    """
    제출된 답변을 기반으로 점수를 계산하여 결과를 반환하고,
    사용자 DB에 유형을 저장합니다. (수정됨)
    """
    
    user_id = submission.user_id
    selected_ids = submission.selected_option_ids
    
    scores = {
        "자기관리형 웰니스족": 0,
        "디지털 트렌드세터": 0,
        "알뜰살뜰 실속파": 0,
        "감성 충만 아티스트": 0,
        "소박한 힐링주의자": 0
    }
    

    for option_id in selected_ids:
        for type_name, scoring_ids in TYPE_SCORING_MAP_COMPLEX.items():
            if option_id in scoring_ids:
                scores[type_name] += 1


    if not scores:
        highest_type_name = "알뜰살뜰 실속파"
    else:
        highest_type_name = max(scores, key=scores.get)
        
        if scores[highest_type_name] == 0:
             highest_type_name = "소박한 힐링주의자" 

    
    final_result_detail = None
    for type_data in ALL_LIFESTYLE_TYPES_DATA:
        if type_data["type_name"] == highest_type_name:
            final_result_detail = type_data
            break
            
    if final_result_detail is None:
        final_result_detail = ALL_LIFESTYLE_TYPES_DATA[2]

    try:

        user_ref = db.collection("users").document(user_id)
        
        user_ref.update({
            "user_lifestyle_type": highest_type_name
        })
    except Exception as e:
        print(f"Error updating user lifestyle type: {e}")

    mock_result = {
        "status": 200,
        "user_id": user_id,
        "result": final_result_detail
    }
    
    return mock_result