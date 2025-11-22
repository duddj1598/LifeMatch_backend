from fastapi import APIRouter, HTTPException, Depends, Body
from app.schemas.lifestyle_test_schema import (
    LifestyleQuestionsResponse,
    LifestyleTypesResponse,
    LifestyleTestSubmission,
    LifestyleTestResultResponse
)
from app.services import lifestyle_test_service
from app.middleware.auth import get_current_user

router = APIRouter(
    prefix="/api/lifestyle-test",
    tags=["Lifestyle Test"]
)


# -------------------------------------------------
# 질문 목록 조회 (JWT 필요 없음)
# -------------------------------------------------
@router.get(
    "/questions",
    response_model=LifestyleQuestionsResponse,
    summary="유형 검사 질문 목록 조회"
)
def get_questions():
    try:
        return lifestyle_test_service.get_test_questions()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"질문 조회 중 오류 발생: {str(e)}")


# -------------------------------------------------
# 전체 라이프스타일 유형 목록 조회
# -------------------------------------------------
@router.get(
    "/types",
    response_model=LifestyleTypesResponse,
    summary="전체 라이프스타일 유형 조회"
)
def get_all_types():
    try:
        return lifestyle_test_service.get_lifestyle_types()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"유형 목록 조회 중 오류 발생: {str(e)}")


# -------------------------------------------------
# 🔒 검사지 제출 → 결과 반환 + Firestore 저장
# -------------------------------------------------
@router.post(
    "/result",
    response_model=LifestyleTestResultResponse,
    summary="유형 검사 결과 제출 및 도출"
)
def submit_test(
    submission: LifestyleTestSubmission = Body(...),
    current_user: dict = Depends(get_current_user)
):
    """
    이제 user_id를 Body로 받지 않음.
    JWT에서 가져온 유저 ID를 기반으로 Firestore에 결과 저장.
    """
    try:
        return lifestyle_test_service.process_test_results(
            current_user["user_doc_id"],   # <-- Firestore 문서 ID
            submission.selected_option_ids
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"결과 처리 중 오류 발생: {str(e)}")
