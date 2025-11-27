from fastapi import APIRouter, HTTPException, Depends
from app.schemas.home_schema import HomeResponse, OtherRecommendationsResponse
from app.services import home_service
from app.middleware.auth import get_current_user

router = APIRouter(
    prefix="/api/home",
    tags=["Home"]
)

# -------------------------------------------------
# 🔒 홈 화면 추천 활동 조회 (본인 정보 기반)
# -------------------------------------------------
@router.get(
    "/recommendations",
    response_model=HomeResponse,
    summary="홈 화면 추천 활동 조회 (기본)"
)
def get_home_data(current_user: dict = Depends(get_current_user)):
    """
    user_id를 프론트로부터 받지 않는다.
    JWT가 가지고 있는 Firestore 문서 ID(user_doc_id)를 사용한다.
    """
    try:
        user_id = current_user["user_doc_id"]
        return home_service.get_home_recommendations(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"데이터 조회 중 오류: {str(e)}")


# -------------------------------------------------
# 🔒 홈 화면 '다른 유형 추천' 조회
# -------------------------------------------------
@router.get(
    "/recommendations/other",
    response_model=OtherRecommendationsResponse,
    summary="다른 라이프스타일 유형 추천 활동 조회"
)
def get_other_home_data(current_user: dict = Depends(get_current_user)):
    try:
        user_id = current_user["user_doc_id"]
        return home_service.get_other_recommendations(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"데이터 조회 중 오류: {str(e)}")
