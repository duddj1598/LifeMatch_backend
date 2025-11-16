from fastapi import APIRouter, HTTPException, Query
from app.schemas.home_schema import HomeResponse, OtherRecommendationsResponse
from app.services import home_service 

router = APIRouter(
    prefix="/api/home", 
    tags=["Home"] 
)

@router.get(
    "/recommendations", 
    response_model=HomeResponse,
    summary="홈 화면 추천 활동 조회 (기본)"
)
def get_home_data(user_id: str = Query(..., description="로그인한 사용자(본인)의 ID")):
    """
    로그인한 사용자의 ID를 기반으로,
    사용자의 라이프스타일 유형과 **맞춤형 추천 활동 2가지**를 반환합니다.
    (로직 보완됨: 2개가 안 될 경우 기본 카테고리에서 채움)
    """
    try:
        results = home_service.get_home_recommendations(user_id)
        return results
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"데이터 조회 중 오류: {str(e)}")


@router.get(
    "/recommendations/other",
    response_model=OtherRecommendationsResponse,
    summary="홈 화면 '다른' 유형 추천 활동 조회"
)
def get_other_home_data(user_id: str = Query(..., description="로그인한 사용자(본인)의 ID")):
    """
    로그인한 사용자의 유형을 *제외한* **'다른' 유형**들에게 추천되는 활동 목록을 반환합니다.
    (사진 속 '다른 유형에게 추천되는 활동 더보기' 기능용)
    """
    try:
        results = home_service.get_other_recommendations(user_id)
        return results
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"데이터 조회 중 오류: {str(e)}")
    