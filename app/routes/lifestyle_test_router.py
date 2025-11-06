# app/routes/lifestyle_test_router.py

from fastapi import APIRouter, HTTPException, Body
from app.schemas.lifestyle_test_schema import (
    LifestyleQuestionsResponse, LifestyleTypesResponse, 
    LifestyleTestSubmission, LifestyleTestResultResponse
)
from app.services import lifestyle_test_service

router = APIRouter(
    prefix="/user", 
    tags=["Lifestyle Test"] # API 문서(Swagger)의 카테고리
)

@router.get(
    "/lifestyle-test/questions", 
    response_model=LifestyleQuestionsResponse,
    summary="유형 검사 질문 목록 조회"
)
def get_questions():
    """
    사용자의 라이프스타일 유형을 파악하기 위한 질문 목록을 조회합니다.
    """
    try:
        results = lifestyle_test_service.get_test_questions()
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"질문 조회 중 오류 발생: {str(e)}")

@router.get(
    "/lifestyle-types",
    response_model=LifestyleTypesResponse,
    summary="전체 라이프스타일 유형 조회"
)
def get_all_types():
    """
    LifeMatch 서비스에서 정의한 전체 라이프스타일 유형의 목록과 설명을 조회합니다.
    """
    try:
        results = lifestyle_test_service.get_lifestyle_types()
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"유형 목록 조회 중 오류 발생: {str(e)}")

@router.post(
    "/lifestyle-test/result",
    response_model=LifestyleTestResultResponse,
    summary="유형 검사 결과 제출 및 도출"
)
def submit_test(submission: LifestyleTestSubmission = Body(...)):
    """
    사용자가 선택한 답변(option_ids)을 제출받아 라이프스타일 유형 검사 결과를 반환합니다.
    """
    try:
        result = lifestyle_test_service.process_test_results(submission)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"결과 처리 중 오류 발생: {str(e)}")